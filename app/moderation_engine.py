"""
Central Moderation Orchestrator

Purpose:
- Run complete moderation workflow.
- Execute selected policies dynamically.
- Persist audit logs/results.
- Trigger final run-level aggregation.

Important:
- This file does NOT contain policy logic.
- Policies are selected from ENABLED_POLICIES or explicit API query.
- Policy execution is handled by POLICY_REGISTRY.
- Module execution is handled inside generic_policy_runner using each policy config.
- M99 final aggregation runs after all policies complete.
"""

from typing import Optional

from app.logger import get_logger
from config.settings import settings

from app.policies.policy_registry import POLICY_REGISTRY
from app.modules.m99_final_aggregation import build_final_moderation_result

from app.modules.module_registry import MODULE_REGISTRY

from app.db import (
    get_project_by_id,
    create_moderation_run,
    update_moderation_run_status,
    insert_moderation_log,
    insert_policy_result,
    insert_final_moderation_result,
    batch_insert_moderation_logs,
    batch_insert_module_results,
)

# Modules executed once per project and shared across all policy runs.
PREPROCESSING_MODULES = ["M01", "M02", "M05"]

logger = get_logger()


def run_shared_preprocessing(project: dict, reference_config: dict) -> dict:
    """
    Run M01, M02, M05 once for the project and return the populated
    shared_artifacts dict. All policies in the same run reuse these
    results instead of recomputing identical text normalization and
    entity extraction N times.
    """
    state = {
        "project": project,
        "shared_artifacts": {},
        "policy_workspace": {"policy_code": "PREPROCESSING", "module_outputs": []},
        "final_result": None
    }

    for module_code in PREPROCESSING_MODULES:
        module_runner = MODULE_REGISTRY.get(module_code)
        if not module_runner:
            logger.warning(f"Preprocessing: module {module_code} not in registry, skipping.")
            continue
        try:
            module_runner(state, reference_config)
            logger.info(f"Shared preprocessing: {module_code} completed.")
        except Exception as exc:
            logger.warning(f"Shared preprocessing: {module_code} failed ({exc}), continuing.")

    return state["shared_artifacts"]


def resolve_policies_to_run(policy_code: Optional[str] = None) -> list[str]:
    """
    Decide which policies should execute.

    Priority:
    1. If policy_code is explicitly passed from API/UI, run only that policy.
    2. Otherwise run all policies configured in ENABLED_POLICIES.

    This keeps the system scalable:
    - Current POC: ENABLED_POLICIES=TYPE-PROJECT-01
    - Future: ENABLED_POLICIES=TYPE-PROJECT-01,LEGAL-01,REG-02,NUIS-04
    """

    if policy_code:
        policies = [policy_code]
    else:
        policies = settings.enabled_policies

    if not policies:
        raise ValueError(
            "No policies configured. Please set ENABLED_POLICIES in .env."
        )

    unknown = [
        policy
        for policy in policies
        if policy not in POLICY_REGISTRY
    ]

    if unknown:
        raise ValueError(
            f"Unknown policy/policies: {unknown}. "
            f"Registered policies: {list(POLICY_REGISTRY.keys())}"
        )

    return policies


def build_execution_message(policy_results: list) -> str:
    """
    Build human-readable execution summary for UI and logs.
    """

    parts = []

    for result in policy_results:
        summary = result.get("execution_summary", {})
        executed = summary.get("modules_executed", [])

        names = [
            f"{m.get('module_code')} ({m.get('module_name')})"
            for m in executed
        ]

        parts.append(
            f"{summary.get('policy_code')} executed: {', '.join(names)}"
        )

    return " | ".join(parts)


def log_module_outputs(
    run_id: int,
    project_id: int,
    selected_policy_code: str,
    policy_result_id: Optional[int],
    module_outputs: list
):
    """
    Persist module audit logs and results in two batched transactions
    (one for ModerationLogs, one for ModuleResults) instead of one
    connection per module.
    """
    log_entries = [
        {
            "run_id":      run_id,
            "project_id":  project_id,
            "policy_code": selected_policy_code,
            "log_level":   "INFO",
            "step_name":   m.get("module_code"),
            "message":     m.get("summary"),
            "details": {
                "module_name":       m.get("module_name"),
                "module_status":     m.get("module_status"),
                "module_outcome":    m.get("module_outcome"),
                "evaluation_status": m.get("evaluation_status"),
                "dependency_gap":    m.get("dependency_gap"),
            },
        }
        for m in module_outputs
    ]

    batch_insert_moderation_logs(log_entries)
    batch_insert_module_results(run_id, policy_result_id, project_id, module_outputs)


def run_moderation(
    project_id: int,
    policy_code: Optional[str] = None
):
    """
    Main moderation entrypoint.

    Full flow:
    1. Resolve policies to run.
    2. Fetch project from Azure SQL.
    3. Create ModerationRuns row.
    4. For each selected policy:
        - Start policy log.
        - Run generic policy runner.
        - Store PolicyResults.
        - Store ModuleResults.
        - Store ModerationLogs for every module.
        - Complete policy log.
    5. Run M99 final aggregation.
    6. Store FinalModerationResults.
    7. Mark ModerationRuns as COMPLETED.
    """

    logger.info(
        f"Moderation started for project_id={project_id}"
    )

    run_id = None
    selected_policy_codes = []
    run_policy_code_label = None

    try:
        selected_policy_codes = resolve_policies_to_run(
            policy_code
        )

        run_policy_code_label = ",".join(
            selected_policy_codes
        )

        project = get_project_by_id(
            project_id
        )

        if not project:
            return {
                "status": "FAILED",
                "message": f"Project {project_id} not found.",
                "projectId": project_id,
                "policyCodes": selected_policy_codes
            }

        run_id = create_moderation_run(
            project_id=project_id,
            policy_code=run_policy_code_label,
            input_snapshot=project
        )

        insert_moderation_log(
            run_id,
            project_id,
            run_policy_code_label,
            "INFO",
            "RUN_START",
            "Moderation run started.",
            {
                "projectName": project.get("ProjectName"),
                "projectStatus": project.get("ProjectStatus"),
                "expectedOutcome": project.get("ExpectedPolicyOutcome"),
                "scope": settings.CONTENT_SCOPE,
                "policies_to_run": selected_policy_codes,
                "llm_enabled": settings.USE_LLM,
                "llm_deployment": settings.AZURE_OPENAI_DEPLOYMENT
            }
        )

        # Run M01/M02/M05 once and share results across every policy.
        first_config = POLICY_REGISTRY[selected_policy_codes[0]]["config"]
        shared_preprocessing = run_shared_preprocessing(project, first_config)
        logger.info("Shared preprocessing completed; reusing across all policies.")

        policy_results = []
        policy_result_ids = []

        for selected_policy_code in selected_policy_codes:
            logger.info(
                f"Running policy: {selected_policy_code}"
            )

            policy_entry = POLICY_REGISTRY[selected_policy_code]
            policy_runner = policy_entry["runner"]
            policy_config = policy_entry["config"]

            insert_moderation_log(
                run_id,
                project_id,
                selected_policy_code,
                "INFO",
                "POLICY_START",
                f"Policy execution started: {selected_policy_code}",
                {
                    "policy_code": selected_policy_code,
                    "policy_name": policy_config.get("policy_name"),
                    "module_sequence": policy_config.get("module_sequence", []),
                    "llm_task": policy_config.get("llm_task", {})
                }
            )

            policy_result = policy_runner(
                project,
                policy_config,
                preprocessing=shared_preprocessing
            )

            policy_results.append(
                policy_result
            )

            final_result = policy_result.get("final_result")
            policy_result_id = None

            if final_result:
                policy_result_id = insert_policy_result(
                    run_id,
                    project_id,
                    final_result
                )

                policy_result_ids.append(
                    policy_result_id
                )

            log_module_outputs(
                run_id=run_id,
                project_id=project_id,
                selected_policy_code=selected_policy_code,
                policy_result_id=policy_result_id,
                module_outputs=policy_result.get("modules", [])
            )

            insert_moderation_log(
                run_id,
                project_id,
                selected_policy_code,
                "INFO",
                "POLICY_COMPLETE",
                f"Policy execution completed: {selected_policy_code}",
                {
                    "policy_status": policy_result.get("policy_status"),
                    "policy_result_id": policy_result_id,
                    "final_action": (
                        final_result.get("suggested_action")
                        if final_result
                        else None
                    ),
                    "risk_level": (
                        final_result.get("severity")
                        if final_result
                        else None
                    ),
                    "matched_rule_id": (
                        final_result.get("matched_rule_id")
                        if final_result
                        else None
                    ),
                    "manual_review_required": (
                        final_result.get("manual_review_required")
                        if final_result
                        else None
                    )
                }
            )

        final_aggregate_result = build_final_moderation_result(
            run_id=run_id,
            project_id=project_id,
            policy_results=policy_results,
            policy_result_ids=policy_result_ids
        )

        final_moderation_result_id = insert_final_moderation_result(
            run_id,
            project_id,
            final_aggregate_result
        )

        update_moderation_run_status(
            run_id,
            "COMPLETED"
        )

        execution_message = build_execution_message(
            policy_results
        )

        insert_moderation_log(
            run_id,
            project_id,
            run_policy_code_label,
            "INFO",
            "RUN_COMPLETE",
            "Moderation run completed successfully.",
            {
                "message": execution_message,
                "policyResultIds": policy_result_ids,
                "finalModerationResultId": final_moderation_result_id,
                "finalOutcome": final_aggregate_result.get("final_outcome"),
                "finalRiskLevel": final_aggregate_result.get("final_risk_level"),
                "finalSuggestedAction": final_aggregate_result.get("final_suggested_action")
            }
        )

        logger.info(
            f"Moderation completed for run_id={run_id}"
        )

        return {
            "status": "COMPLETED",
            "message": execution_message,
            "runId": run_id,
            "projectId": project_id,
            "policyCodes": selected_policy_codes,
            "policyResultIds": policy_result_ids,
            "finalModerationResultId": final_moderation_result_id,
            "projectName": project.get("ProjectName"),
            "expectedOutcome": project.get("ExpectedPolicyOutcome"),
            "finalModerationResult": final_aggregate_result,
            "policyResults": policy_results
        }

    except Exception as e:
        logger.error(
            f"Moderation failed. project_id={project_id}, error={str(e)}",
            exc_info=True
        )

        if run_id:
            update_moderation_run_status(
                run_id,
                "FAILED",
                str(e)
            )

            insert_moderation_log(
                run_id,
                project_id,
                run_policy_code_label,
                "ERROR",
                "MODERATION_FAILED",
                "Moderation failed during execution.",
                {
                    "error": str(e),
                    "projectId": project_id,
                    "policyCodes": selected_policy_codes
                }
            )

        return {
            "status": "FAILED",
            "message": str(e),
            "runId": run_id,
            "projectId": project_id,
            "policyCodes": selected_policy_codes
        }