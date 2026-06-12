"""
M17: Final Result Packaging

Purpose:
- Convert final policy interpretation into a stable moderation output contract.
- Prepare structured output for:
    - DB persistence
    - auditability
    - UI consumption
    - future APIs
    - downstream analytics

Important:
- M17 does NOT decide moderation outcomes.
- M16 already decided the policy result.
- M17 only packages the result consistently.
"""

from app.logger import get_logger

logger = get_logger()


def build_coverage_summary(details: dict) -> dict:
    """
    Creates readable moderation coverage summary.

    Important:
    Never pretend something was verified if it was not.
    """

    input_coverage = details.get(
        "input_coverage",
        {}
    )

    return {
        "text": "ANALYSED",

        "attachments": (
            "AVAILABLE"
            if input_coverage.get("attachments_available")
            else "NOT_PROVIDED"
        ),

        "images": (
            "AVAILABLE"
            if input_coverage.get("images_available")
            else "NOT_PROVIDED"
        ),

        "external_verification": "NOT_PERFORMED"
    }


def run_m17_result_packaging(
    state: dict,
    policy_config: dict
) -> dict:
    """
    Main M17 runner.

    Inputs:
    - final policy interpretation from M16

    Output:
    - final_result stored in state
    - stable result_json contract
    """

    logger.info("M17 started: Final Result Packaging.")

    final_interpretation = (
        state["policy_workspace"]
        .get("final_policy_interpretation")
    )

    if not final_interpretation:
        logger.error(
            "M17 failed because M16 did not produce final interpretation."
        )

        return {
            "module_code": "M17",
            "module_name": "Result Packaging",
            "module_status": "FAILED",
            "module_outcome": "NO_POLICY_INTERPRETATION_FOUND",
            "evaluation_status": "SKIPPED",
            "dependency_gap": (
                "M16 did not produce final policy interpretation."
            ),
            "summary": (
                "Final result could not be packaged."
            ),
            "data": {}
        }

    details = final_interpretation.get(
        "details",
        {}
    )

    result_json = {
        "schema_version": "1.0",

        "policy_code": policy_config["policy_code"],
        "policy_name": policy_config["policy_name"],

        "final_outcome": final_interpretation.get(
            "suggested_action"
        ),

        "risk_level": final_interpretation.get(
            "severity"
        ),

        "moderator_reason_note": final_interpretation.get(
            "moderator_reason_note"
        ),

        "confidence_score": final_interpretation.get(
            "confidence_score"
        ),

        "evaluation_status": final_interpretation.get(
            "evaluation_status"
        ),

        "dependency_gap": final_interpretation.get(
            "dependency_gap"
        ),

        "matched_rule_id": final_interpretation.get(
            "matched_rule_id"
        ),

        "matched_rule_description": final_interpretation.get(
            "matched_rule_description"
        ),

        "claims_detected": details.get(
            "claims",
            []
        ),

        "evidence_issues": details.get(
            "evidence_issues",
            []
        ),

        "signals": {
            "rule_signals": details.get(
                "rule_signals",
                {}
            ),

            "entities": details.get(
                "entities",
                {}
            ),

            "language_info": details.get(
                "language_info",
                {}
            ),

            "input_coverage": details.get(
                "input_coverage",
                {}
            )
        },

        "coverage_summary": build_coverage_summary(
            details
        ),

        "dependency_gaps": details.get(
            "dependency_gaps",
            []
        ),

        "notes": [
            final_interpretation.get(
                "moderator_reason_note"
            )
        ]
    }

    packaged_result = {
        **final_interpretation,
        "result_json": result_json
    }

    state["final_result"] = packaged_result

    output = {
        "module_code": "M17",
        "module_name": "Result Packaging",
        "module_status": "SUCCESS",
        "module_outcome": "FINAL_RESULT_PACKAGED",
        "evaluation_status": packaged_result.get(
            "evaluation_status"
        ),

        "dependency_gap": packaged_result.get(
            "dependency_gap"
        ),

        "summary": (
            "Final policy result packaged with exhaustive explanation."
        ),

        "data": packaged_result
    }

    logger.info("M17 completed.")
    return output