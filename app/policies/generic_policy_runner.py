"""
Generic Policy Runner

Purpose:
- Dynamically executes moderation modules using policy config.
- Supports scalable policy-driven orchestration.
- Distinguishes critical vs non-critical module failures.

BUG FIX (v2):
- Previously received a raw project dict as `state` and never wrapped it
  into the proper state structure. All modules (M01, M02, M03 ...) were
  then calling state["project"] and state["shared_artifacts"] on the raw
  DB dict, causing KeyErrors or silent empty-data execution.
- Now correctly initialises the state dict before the module loop runs.
"""

from app.logger import get_logger
from app.modules.module_registry import MODULE_REGISTRY

logger = get_logger()

CRITICAL_MODULES = {"M01", "M02"}

# Modules whose outputs are shared across all policies in one run.
# When the engine supplies a preprocessing seed, these are skipped.
PREPROCESSING_MODULE_CODES = {"M01", "M02", "M05"}


def run_policy(
    project: dict,
    policy_config: dict,
    preprocessing: dict = None
) -> dict:
    """
    Main generic policy runner.

    Receives the raw project dict from the DB and wraps it into the
    correct state structure before any module runs.

    State contract expected by all modules:
        state["project"]            → raw DB project dict
        state["shared_artifacts"]   → populated by each module in turn
        state["policy_workspace"]   → M16 writes final interpretation here
        state["final_result"]       → M17 writes packaged result here
    """

    policy_code = policy_config["policy_code"]

    logger.info(
        f"Starting policy pipeline: {policy_code}"
    )

    # ------------------------------------------------------------------ #
    # BUG FIX: Wrap the raw project dict into a proper state structure.
    # Previously this was never done, so modules received the bare project
    # dict as state and all state["project"] / state["shared_artifacts"]
    # lookups either raised KeyErrors or silently returned empty data.
    # ------------------------------------------------------------------ #
    state = {
        "project": project,
        # Seed with pre-computed preprocessing artifacts when provided,
        # so M01/M02/M05 don't re-run for every policy in the same run.
        "shared_artifacts": dict(preprocessing) if preprocessing else {},
        "policy_workspace": {
            "policy_code": policy_code,
            "module_outputs": []
        },
        "final_result": None
    }

    module_outputs = []
    modules_executed = []
    modules_skipped = []

    for module_code in policy_config["module_sequence"]:

        logger.info(
            f"Executing module: {module_code}"
        )

        # Skip modules already satisfied by the shared preprocessing pass.
        if preprocessing and module_code in PREPROCESSING_MODULE_CODES:
            stub = {
                "module_code": module_code,
                "module_name": f"{module_code} (shared preprocessing)",
                "module_status": "SKIPPED",
                "module_outcome": "REUSED_FROM_SHARED_PREPROCESSING",
                "evaluation_status": "FULL",
                "dependency_gap": None,
                "summary": f"{module_code} output reused from shared preprocessing step.",
                "data": {}
            }
            module_outputs.append(stub)
            modules_executed.append({
                "module_code": module_code,
                "module_name": stub["module_name"],
                "module_status": "SKIPPED",
                "module_outcome": stub["module_outcome"],
                "evaluation_status": "FULL",
                "dependency_gap": None
            })
            logger.info(f"Module {module_code} skipped — reusing shared preprocessing.")
            continue

        module_runner = MODULE_REGISTRY.get(
            module_code
        )

        if not module_runner:
            error_output = {
                "module_code": module_code,
                "module_name": "Unknown Module",
                "module_status": "FAILED",
                "module_outcome": "MODULE_NOT_REGISTERED",
                "evaluation_status": "PARTIAL",
                "dependency_gap": (
                    f"Module '{module_code}' "
                    f"not found in registry."
                ),
                "summary": (
                    f"Module '{module_code}' "
                    f"is missing from registry."
                ),
                "data": {}
            }

            module_outputs.append(error_output)
            modules_skipped.append({
                "module_code": module_code,
                "reason": "Module not registered"
            })

            logger.error(
                f"Module not registered: {module_code}"
            )

            if module_code in CRITICAL_MODULES:
                logger.error(
                    f"Critical module failure: {module_code}"
                )
                break

            continue

        try:
            output = module_runner(
                state,
                policy_config
            )

            module_outputs.append(output)

            modules_executed.append({
                "module_code": output.get("module_code"),
                "module_name": output.get("module_name"),
                "module_status": output.get("module_status"),
                "module_outcome": output.get("module_outcome"),
                "evaluation_status": output.get("evaluation_status"),
                "dependency_gap": output.get("dependency_gap")
            })

            logger.info(
                f"Module completed: {module_code}"
            )

            if output.get("module_status") == "FAILED":

                logger.error(
                    f"Module returned FAILED status: "
                    f"{module_code}"
                )

                modules_skipped.append({
                    "module_code": module_code,
                    "reason": "Module returned FAILED status"
                })

                if module_code in CRITICAL_MODULES:
                    logger.error(
                        f"Critical module failed: "
                        f"{module_code}"
                    )
                    break

        except Exception as e:

            logger.exception(
                f"Unhandled exception in module "
                f"{module_code}: {str(e)}"
            )

            error_output = {
                "module_code": module_code,
                "module_name": module_code,
                "module_status": "FAILED",
                "module_outcome": "UNHANDLED_EXCEPTION",
                "evaluation_status": "PARTIAL",
                "dependency_gap": str(e),
                "summary": (
                    f"Unhandled exception occurred "
                    f"in {module_code}."
                ),
                "data": {
                    "exception": str(e)
                }
            }

            module_outputs.append(error_output)

            modules_skipped.append({
                "module_code": module_code,
                "reason": str(e)
            })

            if module_code in CRITICAL_MODULES:
                logger.error(
                    f"Stopping pipeline because "
                    f"{module_code} is critical."
                )
                break

            logger.warning(
                f"Continuing pipeline despite "
                f"non-critical module failure: "
                f"{module_code}"
            )

            continue

    # M17 writes the final packaged result into state["final_result"].
    # M16 writes the interpretation into state["policy_workspace"].
    final_result = (
        state.get("final_result")
        or state["policy_workspace"].get("final_policy_interpretation", {})
    )

    policy_status = "COMPLETED" if final_result else "PARTIAL_COMPLETE"

    return {
        "policy_code": policy_code,
        "policy_name": policy_config["policy_name"],
        "policy_status": policy_status,
        "modules": module_outputs,
        "final_result": final_result,

        # Required by moderation_engine.build_execution_message()
        "execution_summary": {
            "policy_code": policy_code,
            "modules_planned": policy_config.get("module_sequence", []),
            "modules_executed": modules_executed,
            "modules_skipped": modules_skipped,
            "status": policy_status
        }
    }