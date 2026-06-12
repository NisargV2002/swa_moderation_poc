"""
M16: Config-Driven Policy Decision Engine

Purpose:
- Convert extracted moderation signals into a final policy interpretation.
- Apply decision rules dynamically from policy_config.
- Avoid hardcoded policy logic inside Python code.

Context additions vs. original:
- llm_content_filtered: bool — True when Azure content filter blocked the
  primary LLM call. LEGAL policy configs use this to distinguish a confirmed
  harmful-content event from a generic LLM technical failure.

New condition types supported in condition_matches():
- min_rule_signal_count: {"key": "<signal_key>", "min": N}
  Passes when len(rule_signals[key]) >= N.
- has_rule_signal: "<signal_key>"
  Passes when rule_signals[signal_key] is truthy (non-empty list or True).
  Note: rule_signals.nested.key dot-path notation already works via the
  existing get_nested_value() fallback — these new types are for convenience.
"""

from app.logger import get_logger

logger = get_logger()


def get_nested_value(data: dict, path: str):
    current = data

    for part in path.split("."):
        if not isinstance(current, dict):
            return None

        current = current.get(part)

    return current


def condition_matches(context: dict, conditions: dict) -> bool:
    if not conditions:
        return True

    if conditions.get("always") is True:
        return True

    for key, expected in conditions.items():
        if key == "always":
            continue

        # ── Built-in count conditions ─────────────────────────────────────
        if key == "min_claims":
            if context.get("claim_count", 0) < expected:
                return False

        elif key == "min_high_risk_claims":
            if context.get("high_risk_claim_count", 0) < expected:
                return False

        elif key == "min_medium_risk_claims":
            if context.get("medium_risk_claim_count", 0) < expected:
                return False

        elif key == "min_evidence_issues":
            if context.get("evidence_issue_count", 0) < expected:
                return False

        # ── New: rule-signal count threshold ─────────────────────────────
        elif key == "min_rule_signal_count":
            # expected = {"key": "threat_terms_found", "min": 3}
            rs          = context.get("rule_signals", {})
            signal_key  = expected.get("key", "")
            min_count   = int(expected.get("min", 1))
            found_list  = rs.get(signal_key, [])
            if len(found_list) < min_count:
                return False

        # ── New: rule-signal truthy check ─────────────────────────────────
        elif key == "has_rule_signal":
            # expected = "has_threat_terms_signal"  (the signal key name)
            rs    = context.get("rule_signals", {})
            value = rs.get(str(expected))
            if not value:
                return False

        # ── Generic dot-path equality check (handles all other keys) ─────
        else:
            actual = get_nested_value(context, key)

            if actual != expected:
                return False

    return True


def classify_claims_by_risk(
    claims: list,
    policy_config: dict
) -> dict:

    risk_groups = (
        policy_config.get(
            "decision_rules",
            {}
        ).get(
            "risk_groups",
            {}
        )
    )

    high_types = set(
        risk_groups.get(
            "high_risk_claim_types",
            []
        )
    )

    medium_types = set(
        risk_groups.get(
            "medium_risk_claim_types",
            []
        )
    )

    high_risk_claims = []
    medium_risk_claims = []
    low_risk_claims = []

    for original_claim in claims:

        claim = dict(original_claim)

        claim_types = set(
            claim.get("claim_types", [])
        )

        if claim_types.intersection(high_types):

            claim["policy_risk_level"] = "HIGH"
            high_risk_claims.append(claim)

        elif claim_types.intersection(medium_types):

            claim["policy_risk_level"] = "MEDIUM"
            medium_risk_claims.append(claim)

        else:

            claim["policy_risk_level"] = "LOW"
            low_risk_claims.append(claim)

    return {
        "high_risk_claims":   high_risk_claims,
        "medium_risk_claims": medium_risk_claims,
        "low_risk_claims":    low_risk_claims
    }


def evaluate_dependency_gaps(
    context: dict,
    policy_config: dict
) -> tuple[list, bool]:
    gap_messages = []
    force_partial = False

    gap_rules = (
        policy_config.get("decision_rules", {})
        .get("dependency_gap_rules", [])
    )

    for rule in gap_rules:
        if condition_matches(
            context,
            rule.get("condition", {})
        ):
            message = rule.get("message")

            if message:
                gap_messages.append(message)

            if rule.get("force_partial_evaluation"):
                force_partial = True

    return sorted(set(gap_messages)), force_partial


def choose_decision(
    context: dict,
    policy_config: dict
) -> dict:
    decision_rules = policy_config.get(
        "decision_rules",
        {}
    )

    default_decision = decision_rules.get(
        "default",
        {}
    )

    for rule in decision_rules.get("rules", []):
        if condition_matches(
            context,
            rule.get("conditions", {}),
        ):
            result = rule.get("result", {}).copy()

            result["matched_rule_id"]          = rule.get("rule_id")
            result["matched_rule_description"] = rule.get("description")

            return result

    result = default_decision.copy()
    result["matched_rule_id"]          = "DEFAULT"
    result["matched_rule_description"] = "Default decision rule."

    return result


def run_m16_policy_decision(
    state: dict,
    policy_config: dict
) -> dict:
    logger.info("M16 started: Config-Driven Policy Decision.")

    claims = state["shared_artifacts"].get("claims", [])

    evidence_analysis = state["shared_artifacts"].get(
        "evidence_analysis",
        {}
    )

    rule_signals = state["shared_artifacts"].get(
        "rule_signals",
        {}
    )

    entities = state["shared_artifacts"].get(
        "entities",
        {}
    )

    language_info = state["shared_artifacts"].get(
        "language_info",
        {}
    )

    input_coverage = state["shared_artifacts"].get(
        "input_coverage",
        {}
    )

    llm_analysis_failed = state["shared_artifacts"].get(
        "llm_analysis_failed",
        False
    )

    llm_failure_reason = state["shared_artifacts"].get(
        "llm_failure_reason"
    )

    # NEW: surface the content-filter flag so decision rules can reference it
    llm_content_filtered = state["shared_artifacts"].get(
        "llm_content_filtered",
        False
    )

    # NEW: surface the LLM's recommended tier so LEGAL configs can use direct
    # tier rules instead of relying on claim-type risk mapping.
    llm_recommended_tier = state["shared_artifacts"].get(
        "llm_recommended_tier",
        None
    )

    evidence_issues = evidence_analysis.get(
        "evidence_issues",
        []
    )

    risk_classification = classify_claims_by_risk(
        claims,
        policy_config
    )

    context = {
        "claim_count": len(claims),
        "evidence_issue_count": len(evidence_issues),

        "high_risk_claim_count": len(
            risk_classification["high_risk_claims"]
        ),

        "medium_risk_claim_count": len(
            risk_classification["medium_risk_claims"]
        ),

        "low_risk_claim_count": len(
            risk_classification["low_risk_claims"]
        ),

        "claims":         claims,
        "evidence_issues": evidence_issues,
        "rule_signals":   rule_signals,
        "entities":       entities,
        "language_info":  language_info,
        "input_coverage": input_coverage,

        "llm_analysis_failed":  llm_analysis_failed,
        "llm_failure_reason":   llm_failure_reason,

        # Exposed for LEGAL policy fallback and tier-direct rules
        "llm_content_filtered":  llm_content_filtered,

        # Exposed for LEGAL policy tier-direct rules
        # e.g. "llm_recommended_tier": "QUARANTINE" -> REJECT_RECOMMENDED
        "llm_recommended_tier":  llm_recommended_tier,
    }

    decision = choose_decision(
        context,
        policy_config
    )

    dependency_gaps, force_partial = evaluate_dependency_gaps(
        context,
        policy_config
    )

    if llm_analysis_failed and llm_failure_reason:
        dependency_gaps.append(
            f"LLM semantic analysis failed: {llm_failure_reason}"
        )
        force_partial = True

    evaluation_status = (
        "PARTIAL"
        if force_partial
        else "FULL"
    )

    final_policy_interpretation = {
        "policy_code": policy_config["policy_code"],
        "policy_name": policy_config["policy_name"],

        "matched_flag": decision.get(
            "matched_flag",
            False
        ),

        "evaluation_status": evaluation_status,

        "severity": decision.get(
            "severity",
            "LOW"
        ),

        "suggested_action": decision.get(
            "suggested_action",
            "PASS"
        ),

        "escalate_to": decision.get(
            "escalate_to"
        ),

        "manual_review_required": decision.get(
            "manual_review_required",
            False
        ),

        "dependency_gap": (
            "; ".join(sorted(set(dependency_gaps)))
            if dependency_gaps
            else None
        ),

        "moderator_reason_note": decision.get(
            "reason_template"
        ),

        "confidence_score": decision.get(
            "confidence_score",
            0.7
        ),

        "matched_rule_id": decision.get(
            "matched_rule_id"
        ),

        "matched_rule_description": decision.get(
            "matched_rule_description"
        ),

        "details": {
            **context,

            "dependency_gaps": sorted(set(dependency_gaps)),

            "risk_classification": risk_classification,

            "decision_context": {
                "matched_rule_id": decision.get(
                    "matched_rule_id"
                ),

                "matched_rule_description": decision.get(
                    "matched_rule_description"
                ),

                "decision_source": (
                    "policy_config.decision_rules"
                )
            }
        }
    }

    state["policy_workspace"]["final_policy_interpretation"] = (
        final_policy_interpretation
    )

    output = {
        "module_code":      "M16",
        "module_name":      "Config-Driven Policy Decision Engine",
        "module_status":    "SUCCESS",
        "module_outcome":   "POLICY_DECISION_CREATED",
        "evaluation_status": evaluation_status,
        "dependency_gap":   final_policy_interpretation.get(
            "dependency_gap"
        ),
        "summary": final_policy_interpretation.get(
            "moderator_reason_note"
        ),
        "data": final_policy_interpretation
    }

    logger.info("M16 completed.")
    return output