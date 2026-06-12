"""
M07: LLM Policy Analysis / Claim Extraction

Purpose:
- Perform semantic claim extraction using the configured LLM.
- Extract explicit, implicit, multilingual, and contextual claims.
- Use rule/entity signals only as support, not as limits.
- Produce normalized claim objects for M08 evidence matching and M16 decision logic.

Content Filter Handling (LEGAL policies):
- When Azure OpenAI's content filter blocks the primary LLM call, this module
  detects the error and performs an ABSTRACTED RETRY using only rule signal
  COUNTS — never the raw harmful text — so the retry itself cannot re-trigger
  the filter.
- The retry returns a synthetic claim whose type is chosen from the policy's
  configured high/medium risk groups based on signal severity.
- This lets M16's existing claim-count decision rules classify correctly even
  when the primary LLM call was blocked.
- If the abstracted retry also fails, M07 sets llm_content_filtered=True and
  llm_analysis_failed=True so M16 can apply its rule-signal fallback rules.

Important:
- M07 does NOT make the final moderation decision.
- M07 extracts and structures claims.
- M16 makes the policy decision using config-driven rules.
"""

from config.settings import settings
from app.logger import get_logger
from app.clients.llm_client import call_llm_json, is_content_filter_error
from app.prompts.prompt_library import PROMPT_LIBRARY

logger = get_logger()

# ─────────────────────────────────────────────────────────────────────────────
# Abstracted retry — sends signal counts only, never raw text
# ─────────────────────────────────────────────────────────────────────────────

_ABSTRACTED_SYSTEM_PROMPT = """You are a moderation severity classifier.

A content safety filter blocked a project submission because the text was flagged as potentially harmful for policy {policy_code}: {policy_name}.

You have been given ONLY the signal counts extracted from that text — NOT the actual content. Your job is to estimate the violation severity based on the signal pattern.

Classification guide:
  CRITICAL  – quarantine_indicator_count > 0  (extreme/targeting content detected)
  HIGH      – quarantine_indicator_count == 0  AND  total_harmful_signal_count >= 2
  LOW       – quarantine_indicator_count == 0  AND  total_harmful_signal_count == 1
  NONE      – all counts are 0  (filter may have false-positived)

High-risk claim types for this policy (use one for CRITICAL):
{high_risk_types}

Medium-risk claim types (use one for HIGH):
{medium_risk_types}

Return ONLY valid JSON — no markdown, no preamble:
{{
  "violation_severity": "NONE|LOW|HIGH|CRITICAL",
  "most_likely_claim_type": "exact_type_string_or_null",
  "confidence": 0.75,
  "reason": "one sentence"
}}

For NONE/LOW, set most_likely_claim_type to null.
For HIGH, pick one type from the medium-risk list above.
For CRITICAL, pick one type from the high-risk list above."""


def _build_abstracted_payload(state: dict, policy_config: dict) -> dict:
    """
    Build a safe signal-count summary for the abstracted retry.
    Contains NO raw text from the submission — only category names and counts.
    """
    rule_signals = state["shared_artifacts"].get("rule_signals", {})
    entities     = state["shared_artifacts"].get("entities", {})

    # Collect counts of matched terms per extra-signal category
    signal_category_counts = {}
    total_harmful = 0
    quarantine_count = 0

    for key, value in rule_signals.items():
        if key.endswith("_found") and isinstance(value, list) and len(value) > 0:
            category = key.replace("_found", "")
            count = len(value)
            signal_category_counts[category] = count
            # Track quarantine and general harmful counts separately
            if "quarantine_indicator" in category:
                quarantine_count += count
            elif category not in ("numbers", "urls", "emails",
                                   "absolute_terms", "evidence_terms",
                                   "authority_terms"):
                total_harmful += count

    # Entity presence flags (safe — just booleans, no actual names)
    entity_flags = {
        "has_named_persons":    bool(entities.get("persons")),
        "has_named_locations":  bool(entities.get("locations")),
        "has_organisations":    bool(entities.get("organisations")),
        "has_email_addresses":  bool(rule_signals.get("has_email_signal", False)),
        "has_urls":             bool(rule_signals.get("has_url_signal", False)),
    }

    return {
        "note": (
            "Raw submission text was blocked by Azure content filter. "
            "Classify based on signal counts only."
        ),
        "quarantine_indicator_count": quarantine_count,
        "total_harmful_signal_count": total_harmful,
        "signal_category_counts":     signal_category_counts,
        "entity_flags":               entity_flags,
        "language": (
            state["shared_artifacts"]
            .get("language_info", {})
            .get("detected_language", "unknown")
        ),
    }


def _try_abstracted_classification(
    state: dict,
    policy_config: dict,
) -> tuple[list, bool]:
    """
    Attempt a content-filter-safe LLM classification using signal counts only.

    Returns:
        (claims_list, success_flag)
        - claims_list: list of zero or one synthetic claim objects
        - success_flag: True if the call completed (even if violation_severity=NONE)
    """
    policy_code   = policy_config.get("policy_code", "UNKNOWN")
    policy_name   = policy_config.get("policy_name", "")
    decision_rules = policy_config.get("decision_rules", {})
    risk_groups    = decision_rules.get("risk_groups", {})
    high_risk      = risk_groups.get("high_risk_claim_types",   [])
    medium_risk    = risk_groups.get("medium_risk_claim_types", [])
    all_claim_types = policy_config.get("claim_types", [])

    # Find a "safe" low-risk claim type (not in high or medium lists)
    low_risk_type = "unclassified_signal"
    high_and_medium = set(high_risk + medium_risk)
    for ct in all_claim_types:
        if ct not in high_and_medium:
            low_risk_type = ct
            break

    system_prompt = _ABSTRACTED_SYSTEM_PROMPT.format(
        policy_code=policy_code,
        policy_name=policy_name,
        high_risk_types=high_risk,
        medium_risk_types=medium_risk,
    )

    payload = _build_abstracted_payload(state, policy_config)

    try:
        response = call_llm_json(
            system_prompt=system_prompt,
            payload=payload,
            max_tokens=300,
        )
    except Exception as exc:
        logger.warning(f"M07 abstracted retry also failed: {exc}")
        return [], False

    severity      = (response.get("violation_severity") or "HIGH").upper()
    claim_type    = response.get("most_likely_claim_type")
    confidence    = float(response.get("confidence") or 0.75)
    reason        = response.get("reason") or "Signal-based classification after content filter event."

    logger.info(
        f"M07 abstracted retry result: severity={severity}, "
        f"claim_type={claim_type}, confidence={confidence}"
    )

    if severity == "NONE" or not claim_type:
        # No violation detected → return empty claims list (→ PASS via default rule)
        return [], True

    # ── Normalise claim type to one from the policy's lists ──────────────
    if severity == "CRITICAL":
        resolved_type = (claim_type if claim_type in high_risk
                         else (high_risk[0] if high_risk else claim_type))
    elif severity == "HIGH":
        resolved_type = (claim_type if claim_type in medium_risk
                         else (medium_risk[0] if medium_risk else claim_type))
    else:
        # LOW — use a claim type that is NOT in high or medium so M16's
        # min_claims: 1 rule returns REVIEW (not ESCALATE/REJECT).
        resolved_type = (claim_type
                         if claim_type and claim_type not in high_and_medium
                         else low_risk_type)

    synthetic_claim = {
        "claim_id":             1,
        "field_name":           "submission_text",
        "span_id":              1,
        "claim_text":           f"[Signal-based assessment: {reason}]",
        "policy_relevant":      True,
        "claim_type":           resolved_type,
        "claim_types":          [resolved_type],
        "claim_strength":       (
            "high"   if severity == "CRITICAL" else
            "medium" if severity == "HIGH"     else
            "low"
        ),
        "temporal_nature":      "current_or_completed_factual",
        "is_factual_claim":     True,
        "is_future_intention":  False,
        "measurable_claim_flag": False,
        "evidence_required":    False,
        "evidence_needed":      False,
        "why_evidence_required": None,
        "risk_reason":          reason,
        "confidence_score":     confidence,
        "detection_method":     "signal_based_classification",
    }

    return [synthetic_claim], True


# ─────────────────────────────────────────────────────────────────────────────
# Claim normalisation (unchanged from original)
# ─────────────────────────────────────────────────────────────────────────────

def normalize_claims(raw_claims: list) -> list:
    """
    Normalize LLM claims into stable internal schema.

    Filters out:
    - explicitly non-policy-relevant claims
    - ordinary activity descriptions
    - future goals
    - aspirational statements
    """

    normalized = []

    for claim in raw_claims or []:

        if claim.get("policy_relevant") is False:
            continue

        temporal_nature = claim.get(
            "temporal_nature",
            "unclear"
        )

        # Only filter by temporal_nature when LLM hasn't explicitly marked as policy_relevant.
        # REG-02 guarantee/absolute claims are inherently future-oriented but still violations.
        if claim.get("policy_relevant") is not True:
            if temporal_nature in [
                "ordinary_activity_or_description",
                "future_or_aspirational"
            ]:
                continue

        claim_types = claim.get("claim_types")

        if not claim_types:
            single_type = claim.get("claim_type")
            claim_types = [single_type] if single_type else ["other"]

        confidence = claim.get(
            "confidence_score",
            0.75
        )

        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.75

        evidence_required = bool(
            claim.get("evidence_required", False)
        )

        normalized.append({
            "claim_id": claim.get("claim_id")
                        or len(normalized) + 1,

            "field_name": claim.get("field_name"),

            "span_id": claim.get("span_id"),

            "claim_text": claim.get("claim_text"),

            "claim_excerpt": claim.get("claim_text"),

            "policy_relevant": True,

            "claim_type": claim.get("claim_type")
                           or claim_types[0],

            "claim_types": claim_types,

            "claim_strength": claim.get(
                "claim_strength",
                "medium"
            ),

            "temporal_nature": temporal_nature,

            "is_factual_claim": bool(
                claim.get("is_factual_claim", False)
            ),

            "is_future_intention": bool(
                claim.get("is_future_intention", False)
            ),

            "measurable_claim_flag": bool(
                claim.get("measurable_claim_flag", False)
            ),

            "evidence_required": evidence_required,

            "evidence_needed": evidence_required,

            "why_evidence_required": claim.get(
                "why_evidence_required"
            ),

            "risk_reason": claim.get(
                "risk_reason"
            ),

            "confidence_score": confidence,

            "detection_method": "llm_semantic_extraction"
        })

    return normalized


# ─────────────────────────────────────────────────────────────────────────────
# Main module runner
# ─────────────────────────────────────────────────────────────────────────────

def run_m07_llm_policy_analysis(
    state: dict,
    policy_config: dict
) -> dict:
    """
    Main M07 runner.

    Happy path: LLM call succeeds → normalized claims stored in shared_artifacts.
    Content filter path: primary call blocked → abstracted retry with signal
      counts only → synthetic claims if violation detected.
    Full failure path: both calls fail → llm_analysis_failed flag set so M16
      rule-signal fallback rules can take over.
    """

    logger.info("M07 started: LLM Policy Analysis.")

    # Reset failure flags at start.
    state["shared_artifacts"]["llm_analysis_failed"]  = False
    state["shared_artifacts"]["llm_failure_reason"]   = None
    state["shared_artifacts"]["llm_content_filtered"] = False

    llm_task  = policy_config.get("llm_task", {})
    prompt_id = llm_task.get("prompt_id")

    if not settings.USE_LLM or not llm_task.get("enabled"):
        state["shared_artifacts"]["claims"]             = []
        state["shared_artifacts"]["llm_analysis_failed"]  = True
        state["shared_artifacts"]["llm_failure_reason"]   = (
            "LLM disabled or policy llm_task disabled."
        )

        output = {
            "module_code":      "M07",
            "module_name":      "LLM Policy Analysis",
            "module_status":    "SKIPPED",
            "module_outcome":   "LLM_DISABLED",
            "evaluation_status": "SKIPPED",
            "dependency_gap":   (
                "LLM is disabled or policy config has llm_task disabled."
            ),
            "summary":          "LLM semantic extraction was skipped.",
            "data": {
                "claim_count": 0,
                "claims":      [],
                "llm_enabled": False
            }
        }

        logger.warning("M07 skipped because LLM is disabled.")
        return output

    prompt_config = PROMPT_LIBRARY.get(prompt_id)

    if not prompt_config:
        error = f"Prompt ID not found in PROMPT_LIBRARY: {prompt_id}"

        state["shared_artifacts"]["claims"]             = []
        state["shared_artifacts"]["llm_analysis_failed"]  = True
        state["shared_artifacts"]["llm_failure_reason"]   = error

        raise ValueError(error)

    payload = {
        "policy": {
            "policy_code":              policy_config.get("policy_code"),
            "policy_name":              policy_config.get("policy_name"),
            "claim_types":              policy_config.get("claim_types"),
            "expected_output_contract": prompt_config.get("output_contract")
        },
        "input": {
            "field_text_map":  state["shared_artifacts"].get("field_text_map", {}),
            "language_info":   state["shared_artifacts"].get("language_info", {}),
            "input_coverage":  state["shared_artifacts"].get("input_coverage", {})
        },
        "support_signals": {
            "rule_signals": state["shared_artifacts"].get("rule_signals", {}),
            "entities":     state["shared_artifacts"].get("entities", {})
        },
        "instruction": (
            "Extract claims exhaustively. Support signals are hints only. "
            "Do not ignore claims just because rule signals are empty. "
            "Do not invent claims that are not supported by the provided project text."
        )
    }

    # ── Primary LLM call ──────────────────────────────────────────────────
    try:
        llm_response = call_llm_json(
            system_prompt=prompt_config["system_prompt"],
            payload=payload,
            max_tokens=llm_task.get("max_tokens", 2200)
        )

        claims = normalize_claims(
            llm_response.get("claims", [])
        )

        state["shared_artifacts"]["claims"]                    = claims
        state["shared_artifacts"]["llm_policy_analysis_raw"]   = llm_response
        state["shared_artifacts"]["llm_analysis_failed"]       = False
        state["shared_artifacts"]["llm_failure_reason"]        = None
        state["shared_artifacts"]["llm_content_filtered"]      = False

        # ── Capture the LLM's tier recommendation so M16 rules can use it ──
        # The LEGAL prompts ask the LLM for recommended_tier which is the most
        # direct signal for correct classification. Storing it here lets M16
        # tier-based rules fire BEFORE claim-type-based rules, avoiding the
        # problem where both ESCALATE and QUARANTINE content maps to the same
        # high-risk claim type (explicit_threat_of_violence) and both become
        # REJECT_RECOMMENDED.
        raw_tier = (llm_response.get("recommended_tier") or "").strip().upper()
        if raw_tier in ("PASS", "NEEDS_REVIEW", "ESCALATE", "QUARANTINE"):
            state["shared_artifacts"]["llm_recommended_tier"] = raw_tier
        else:
            state["shared_artifacts"]["llm_recommended_tier"] = None

        output = {
            "module_code":      "M07",
            "module_name":      "LLM Policy Analysis",
            "module_status":    "SUCCESS",
            "module_outcome":   "CLAIMS_EXTRACTED",
            "evaluation_status": "FULL",
            "dependency_gap":   None,
            "summary":          (
                f"{len(claims)} semantic claim(s) extracted by LLM."
            ),
            "data": {
                "claim_count":  len(claims),
                "claims":       claims,
                "overall_claim_extraction_notes": llm_response.get(
                    "overall_claim_extraction_notes"
                ),
                "language_handling_notes": llm_response.get(
                    "language_handling_notes"
                ),
                "llm_enabled":  True
            }
        }

        logger.info("M07 completed successfully.")
        return output

    except Exception as primary_exc:

        # ── Content filter branch ─────────────────────────────────────────
        if is_content_filter_error(primary_exc):
            logger.warning(
                f"M07 primary call blocked by Azure content filter: {primary_exc}. "
                "Attempting abstracted signal-based retry."
            )
            state["shared_artifacts"]["llm_content_filtered"] = True

            # Abstracted retry — sends only signal counts, no harmful text
            synthetic_claims, retry_ok = _try_abstracted_classification(
                state, policy_config
            )

            if retry_ok:
                if not synthetic_claims:
                    # Abstracted retry returned NONE/LOW severity — no actionable signal.
                    # The Azure content filter DID fire (violence=medium confirmed),
                    # so defaulting to PASS would silently clear genuinely harmful
                    # content. Set llm_analysis_failed so M16 R0b safety rule fires
                    # (→ ESCALATE) instead of falling through to DEFAULT → PASS.
                    logger.warning(
                        "M07 abstracted retry returned no actionable claim (NONE/LOW). "
                        "Content filter fired — setting llm_analysis_failed=True so "
                        "M16 R0a/R0b safety rules apply instead of DEFAULT → PASS."
                    )
                    failure_reason = (
                        "Content filter fired; abstracted retry returned no actionable "
                        "severity. M16 R0b safety rule will classify (→ ESCALATE)."
                    )
                    state["shared_artifacts"]["claims"]               = []
                    state["shared_artifacts"]["llm_analysis_failed"]  = True
                    state["shared_artifacts"]["llm_failure_reason"]   = failure_reason
                    state["shared_artifacts"]["llm_recommended_tier"] = None

                    return {
                        "module_code":      "M07",
                        "module_name":      "LLM Policy Analysis",
                        "module_status":    "PARTIAL",
                        "module_outcome":   "CONTENT_FILTER_NO_SIGNAL",
                        "evaluation_status": "PARTIAL",
                        "dependency_gap":   failure_reason,
                        "summary":          failure_reason,
                        "data": {
                            "claim_count":             0,
                            "claims":                  [],
                            "content_filter_fired":    True,
                            "abstracted_retry_used":   True,
                            "abstracted_retry_result": "NO_ACTIONABLE_SIGNAL",
                            "llm_enabled":             True
                        }
                    }

                # Retry succeeded AND returned at least one actionable synthetic claim
                state["shared_artifacts"]["claims"]               = synthetic_claims
                state["shared_artifacts"]["llm_analysis_failed"]  = False
                state["shared_artifacts"]["llm_failure_reason"]   = None

                # Derive tier from the synthetic claim's risk group membership
                _ct   = synthetic_claims[0].get("claim_type", "")
                _high = set(policy_config.get("decision_rules", {}).get("risk_groups", {}).get("high_risk_claim_types", []))
                _med  = set(policy_config.get("decision_rules", {}).get("risk_groups", {}).get("medium_risk_claim_types", []))
                if _ct in _high:
                    state["shared_artifacts"]["llm_recommended_tier"] = "QUARANTINE"
                elif _ct in _med:
                    state["shared_artifacts"]["llm_recommended_tier"] = "ESCALATE"
                else:
                    state["shared_artifacts"]["llm_recommended_tier"] = "NEEDS_REVIEW"

                detection_note = (
                    "Content filter blocked primary call. "
                    f"Abstracted signal retry returned {len(synthetic_claims)} synthetic claim(s)."
                )
                logger.info(detection_note)

                return {
                    "module_code":      "M07",
                    "module_name":      "LLM Policy Analysis",
                    "module_status":    "PARTIAL",
                    "module_outcome":   "SIGNAL_BASED_CLAIMS",
                    "evaluation_status": "PARTIAL",
                    "dependency_gap":   detection_note,
                    "summary":          detection_note,
                    "data": {
                        "claim_count":          len(synthetic_claims),
                        "claims":               synthetic_claims,
                        "content_filter_fired": True,
                        "abstracted_retry_used": True,
                        "llm_enabled":          True
                    }
                }

            # Retry also failed — fall through to full failure path
            logger.warning(
                "M07 abstracted retry also failed. Setting llm_analysis_failed=True "
                "so M16 rule-signal fallback rules can classify."
            )
            failure_reason = (
                f"Content filter blocked LLM call AND abstracted retry failed: {primary_exc}"
            )

        else:
            # Non-content-filter failure (network, timeout, bad JSON, etc.)
            failure_reason = str(primary_exc)

        logger.error(
            f"M07 LLM analysis failed: {failure_reason}",
            exc_info=True
        )

        state["shared_artifacts"]["claims"]             = []
        state["shared_artifacts"]["llm_analysis_failed"]  = True
        state["shared_artifacts"]["llm_failure_reason"]   = failure_reason

        return {
            "module_code":      "M07",
            "module_name":      "LLM Policy Analysis",
            "module_status":    "FAILED",
            "module_outcome":   "LLM_ANALYSIS_FAILED",
            "evaluation_status": "PARTIAL",
            "dependency_gap":   failure_reason,
            "summary":          "LLM analysis failed — rule-signal fallback will apply.",
            "data": {
                "claim_count":          0,
                "claims":               [],
                "error":                failure_reason,
                "content_filter_fired": state["shared_artifacts"].get(
                    "llm_content_filtered", False
                ),
                "llm_enabled":          True
            }
        }