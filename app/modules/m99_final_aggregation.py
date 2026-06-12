"""
M99: Final Moderation Aggregation

Purpose:
- Combine all policy-level moderation results into one final moderation outcome.
- Produce final moderation summary for:
    - UI
    - DB persistence
    - downstream APIs
    - reporting/audit

Important:
- M99 runs AFTER all policies complete.
- M99 is NOT a policy-level module.
- M99 is run-level aggregation logic.

Why separate from policy modules?
- M01–M17 operate inside one policy pipeline.
- M99 combines ALL policies together.
"""

from app.logger import get_logger

logger = get_logger()


ACTION_PRIORITY = [
    "REJECT_RECOMMENDED",
    "ESCALATE",
    "REQUEST_AMENDMENT",
    "REVIEW",
    "PASS"
]

RISK_PRIORITY = [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW"
]


def pick_highest_priority(
    values: list,
    priority: list,
    default: str
):
    """
    Select highest-priority value based on ordered priority list.
    """

    clean_values = [
        value for value in values
        if value
    ]

    for item in priority:
        if item in clean_values:
            return item

    return default


def build_policy_summary(final: dict) -> dict:
    """
    Create clean per-policy summary.
    """

    details = final.get("details", {})

    return {
        "policy_code": final.get("policy_code"),
        "policy_name": final.get("policy_name"),

        "outcome": final.get("suggested_action"),

        "risk_level": final.get("severity"),

        "summary": final.get(
            "moderator_reason_note"
        ),

        "claim_count": details.get(
            "claim_count"
        ),

        "evidence_issue_count": details.get(
            "evidence_issue_count"
        ),

        "matched_rule_id": final.get(
            "matched_rule_id"
        )
    }


def build_final_moderation_result(
    run_id,
    project_id,
    policy_results: list,
    policy_result_ids: list
):
    """
    Main M99 aggregation function.
    """

    logger.info("M99 started: Final Moderation Aggregation.")

    actions = [
        result.get("final_result", {}).get(
            "suggested_action"
        )
        for result in policy_results
    ]

    risks = [
        result.get("final_result", {}).get(
            "severity"
        )
        for result in policy_results
    ]

    final_action = pick_highest_priority(
        actions,
        ACTION_PRIORITY,
        "PASS"
    )

    final_risk = pick_highest_priority(
        risks,
        RISK_PRIORITY,
        "LOW"
    )

    triggered_policies = []
    dependency_gaps = []
    policy_summaries = []

    request_evidence_flag = False
    escalation_flag = False
    human_decision_required = False

    for result in policy_results:
        final = result.get("final_result") or {}

        if final.get("matched_flag"):
            triggered_policies.append(
                final.get("policy_code")
            )

        if final.get("suggested_action") == "REQUEST_AMENDMENT":
            request_evidence_flag = True

        if final.get("suggested_action") == "ESCALATE":
            escalation_flag = True

        if final.get("manual_review_required"):
            human_decision_required = True

        if final.get("dependency_gap"):
            dependency_gaps.append(
                final.get("dependency_gap")
            )

        policy_summaries.append(
            build_policy_summary(final)
        )

    if triggered_policies:
        final_reason = (
            "Final moderation outcome was determined using "
            "triggered policy results from: "
            + ", ".join(triggered_policies)
            + "."
        )
    else:
        final_reason = (
            "No policy produced a blocking moderation concern."
        )

    moderator_reason_note = " ".join(
        summary.get("summary") or ""
        for summary in policy_summaries
        if summary.get("summary")
    ).strip()

    final_output_json = {
        "schema_version": "1.0",

        "run_id": run_id,
        "project_id": project_id,

        "final_outcome": final_action,
        "final_risk_level": final_risk,

        "triggered_policies": triggered_policies,

        "policy_result_ids": policy_result_ids,

        "policy_summaries": policy_summaries,

        "dependency_gaps": sorted(
            set(dependency_gaps)
        ),

        "aggregation_logic": {
            "action_priority": ACTION_PRIORITY,
            "risk_priority": RISK_PRIORITY,
            "aggregation_method": (
                "highest_priority_policy_result"
            )
        }
    }

    result = {
        "final_outcome": final_action,

        "final_risk_level": final_risk,

        "final_suggested_action": final_action,

        "final_reason": final_reason,

        "moderator_reason_note": (
            moderator_reason_note
            or final_reason
        ),

        "request_evidence_flag": request_evidence_flag,

        "escalation_flag": escalation_flag,

        "human_decision_required": (
            human_decision_required
        ),

        "final_output_json": final_output_json
    }

    logger.info("M99 completed.")
    return result