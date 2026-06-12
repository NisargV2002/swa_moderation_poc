"""
M03: Deterministic Rule Signal Extraction

Purpose:
- Extract cheap, explainable support signals from project text.
- These signals are support hints for M07 (LLM) and M16 (decision engine).
- This module does NOT make moderation decisions.

Scalability design:
- All term lists are read from policy_config, so M03 is fully reusable
  across policies without modification.
- Any future policy can add new term list keys to its config and M03
  will automatically pick them up via EXTRA_TERM_LIST_KEYS.

Current EXTRA_TERM_LIST_KEYS coverage:
  REG-01:   distortion_terms, environmental_terms
  REG-02:   superlative_trigger_terms, certification_terms,
            exclusivity_terms, guarantee_terms
  REG-03:   privacy_violation_terms
  REG-04:   promotional_disclosure_terms
  LEGAL-01: threat_terms, extortion_terms, quarantine_indicator_terms
  LEGAL-02: pii_indicator_terms, quarantine_indicator_terms
  LEGAL-03: allegation_terms, quarantine_indicator_terms
  LEGAL-05: legal_confidentiality_terms, quarantine_indicator_terms
  MAL-01:   phishing_terms, urgency_terms
  MAL-02:   malware_terms, executable_terms
  MAL-03:   impersonation_terms
  MAL-04:   abuse_pattern_terms
  NUIS-01:  spam_terms
  NUIS-02:  placeholder_terms
  NUIS-03:  off_topic_indicators
  NUIS-04:  formatting_abuse_terms
  OFF-01:   hate_terms
  OFF-02:   harassment_terms
  OFF-03:   obscenity_terms

quarantine_indicator_terms (added to each LEGAL config):
  Used by M16 fallback rule R0a to distinguish QUARANTINE-severity content
  (→ REJECT_RECOMMENDED) from ESCALATE-severity content when the primary
  LLM call is blocked by Azure's content filter.
  These terms are deliberately specific — they should only appear in
  genuinely QUARANTINE-level submissions, not in PASS / NEEDS_REVIEW /
  ESCALATE cases.
"""

import re
from app.logger import get_logger

logger = get_logger()

# All config-level term list keys that M03 will scan if present in the policy config.
# Add new keys here when new policy configs introduce additional term families.
EXTRA_TERM_LIST_KEYS = [
    # REG-01
    "distortion_terms",
    "environmental_terms",
    # REG-02
    "superlative_trigger_terms",
    "certification_terms",
    "exclusivity_terms",
    "guarantee_terms",
    # REG-03
    "privacy_violation_terms",
    # REG-04
    "promotional_disclosure_terms",
    # LEGAL-01
    "threat_terms",
    "extortion_terms",
    "quarantine_indicator_terms",   # NEW — LEGAL-01 targeting/operational signals
    # LEGAL-02
    "pii_indicator_terms",
    # NOTE: quarantine_indicator_terms shared key, registered once above,
    #       works for LEGAL-02/03/05 configs that also define this key.
    # LEGAL-03
    "allegation_terms",
    # LEGAL-05
    "legal_confidentiality_terms",
    # MAL-01
    "phishing_terms",
    "urgency_terms",
    # MAL-02
    "malware_terms",
    "executable_terms",
    # MAL-03
    "impersonation_terms",
    # MAL-04
    "abuse_pattern_terms",
    # NUIS-01
    "spam_terms",
    # NUIS-02
    "placeholder_terms",
    # NUIS-03
    "off_topic_indicators",
    # NUIS-04
    "formatting_abuse_terms",
    # OFF-01
    "hate_terms",
    # OFF-02
    "harassment_terms",
    # OFF-03
    "obscenity_terms",
]


def find_terms(text_lower: str, terms: list) -> list:
    """
    Safe word-boundary term matching.
    Prevents false positives like 'un' matching inside unrelated words.
    """
    found = []
    for term in terms:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.append(term)
    return sorted(set(found))


def run_m03_rule_signals(state: dict, policy_config: dict) -> dict:
    """
    Extract deterministic rule signals from actual field text only.
    Scans user/client text, never field labels.
    Term lists are read from policy_config — fully reusable across all policies.
    """

    logger.info("M03 started: Deterministic Rule Signal Extraction.")

    field_text_map = state["shared_artifacts"].get("field_text_map", {})
    text_only = "\n\n".join(field_text_map.values())
    text_lower = text_only.lower()

    absolute_terms = find_terms(
        text_lower, policy_config.get("absolute_claim_terms", [])
    )
    evidence_terms = find_terms(
        text_lower, policy_config.get("evidence_indicators", [])
    )
    authority_terms = find_terms(
        text_lower, policy_config.get("authority_terms", [])
    )

    numbers = re.findall(
        r"\b\d+(?:\.\d+)?\s?%?\b|\b\d{1,3}(?:,\d{3})+\b",
        text_only
    )
    urls    = re.findall(r"https?://[^\s]+|www\.[^\s]+", text_only)
    emails  = re.findall(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", text_only)

    # Policy-config-driven extra term lists (fully generic)
    extra_signals = {}
    for key in EXTRA_TERM_LIST_KEYS:
        terms = policy_config.get(key, [])
        if terms:
            found = find_terms(text_lower, terms)
            extra_signals[f"{key}_found"]      = found
            extra_signals[f"has_{key}_signal"] = len(found) > 0

    rule_signals = {
        "numbers_found":               numbers,
        "urls_found":                  urls,
        "emails_found":                emails,
        "absolute_terms_found":        absolute_terms,
        "evidence_terms_found":        evidence_terms,
        "authority_terms_found":       authority_terms,
        "has_numeric_claim_signal":    len(numbers) > 0,
        "has_url_signal":              len(urls) > 0,
        "has_email_signal":            len(emails) > 0,
        "has_absolute_wording_signal": len(absolute_terms) > 0,
        "has_authority_signal":        len(authority_terms) > 0,
        "rule_scope_note": (
            "Rules extract deterministic support signals only. "
            "LLM performs independent semantic claim extraction."
        ),
        **extra_signals
    }

    state["shared_artifacts"]["rule_signals"] = rule_signals

    output = {
        "module_code":      "M03",
        "module_name":      "Deterministic Rule Signal Extraction",
        "module_status":    "SUCCESS",
        "module_outcome":   "RULE_SIGNALS_EXTRACTED",
        "evaluation_status": "FULL",
        "dependency_gap":   None,
        "summary":          "Deterministic support signals extracted from project text.",
        "data":             rule_signals
    }

    logger.info("M03 completed.")
    return output