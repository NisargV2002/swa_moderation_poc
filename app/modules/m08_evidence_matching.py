"""
M08: Evidence Detection and Claim Matching

Purpose:
- Check whether extracted claims have supporting evidence references.
- Match evidence near claim spans where possible.
- Detect text evidence signals such as URLs, reports, certificates, references.
- Track attachment/image evidence coverage clearly.

Important:
- This module does NOT verify external authenticity.
- This module does NOT pretend attachments/images were checked if not provided.
- It distinguishes:
    1. Evidence found in text
    2. Evidence missing in text
    3. Attachment/image evidence not provided
    4. External verification not performed
"""

import re

from app.logger import get_logger

logger = get_logger()


def extract_urls(text: str) -> list:
    """
    Extract URLs from provided text.
    """

    return re.findall(
        r"https?://[^\s]+|www\.[^\s]+",
        text or ""
    )


def find_evidence_terms(text: str, evidence_indicators: list) -> list:
    """
    Find evidence-related words/phrases using safe word-boundary matching.
    """

    lower = (text or "").lower()
    found = []

    for term in evidence_indicators:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"

        if re.search(pattern, lower):
            found.append(term)

    return sorted(set(found))


def get_nearby_text_for_claim(claim: dict, spans: list, window_size: int = 1) -> str:
    """
    Builds nearby context around the claim span.

    Why:
    - Evidence is usually near the claim.
    - We avoid treating a random URL anywhere in the project as evidence for every claim.
    """

    claim_span_id = claim.get("span_id")

    if claim_span_id is None:
        return ""

    try:
        claim_span_id = int(claim_span_id)
    except (TypeError, ValueError):
        return ""

    nearby_spans = [
        span for span in spans
        if abs(span.get("span_id", 0) - claim_span_id) <= window_size
    ]

    return " ".join(
        span.get("original_text", "")
        for span in nearby_spans
    )


def build_evidence_status(
    evidence_needed: bool,
    text_evidence_present: bool
) -> str:
    """
    Convert evidence flags into readable status.
    """

    if evidence_needed and not text_evidence_present:
        return "MISSING_IN_TEXT"

    if evidence_needed and text_evidence_present:
        return "TEXT_EVIDENCE_REFERENCE_FOUND_NOT_VERIFIED"

    return "NOT_REQUIRED_OR_LOW_RISK"


def run_m08_evidence_matching(state: dict, policy_config: dict) -> dict:
    """
    Main M08 runner.

    Inputs:
    - claims from M07
    - sentence spans from M02
    - evidence indicators from policy config
    - input coverage from M01

    Output:
    - evidence analysis stored in shared_artifacts
    """

    logger.info("M08 started: Evidence Detection and Claim Matching.")

    normalized_text = state["shared_artifacts"].get("normalized_text", "")
    spans = state["shared_artifacts"].get("sentence_spans", [])
    claims = state["shared_artifacts"].get("claims", [])
    input_coverage = state["shared_artifacts"].get("input_coverage", {})

    evidence_indicators = policy_config.get("evidence_indicators", [])

    global_urls = extract_urls(normalized_text)
    global_evidence_terms = find_evidence_terms(
        normalized_text,
        evidence_indicators
    )

    attachments_available = bool(
        input_coverage.get("attachments_available")
    )

    images_available = bool(
        input_coverage.get("images_available")
    )

    claim_evidence_results = []

    for claim in claims:
        nearby_text = get_nearby_text_for_claim(
            claim,
            spans,
            window_size=1
        )

        nearby_urls = extract_urls(nearby_text)
        nearby_terms = find_evidence_terms(
            nearby_text,
            evidence_indicators
        )

        text_evidence_present = bool(
            nearby_urls or nearby_terms
        )

        evidence_needed = bool(
            claim.get(
                "evidence_needed",
                claim.get("evidence_required", True)
            )
        )

        evidence_status = build_evidence_status(
            evidence_needed=evidence_needed,
            text_evidence_present=text_evidence_present
        )

        claim_evidence_results.append({
            "claim_id": claim.get("claim_id"),
            "claim_excerpt": claim.get("claim_excerpt") or claim.get("claim_text"),
            "field_name": claim.get("field_name"),
            "span_id": claim.get("span_id"),
            "claim_types": claim.get("claim_types", []),
            "evidence_needed": evidence_needed,
            "text_evidence_present_flag": text_evidence_present,
            "evidence_status": evidence_status,
            "evidence_match_scope": "nearby_span_window",
            "evidence_reference_mentions": nearby_terms,
            "urls_found_near_claim": nearby_urls,
            "attachments_available": attachments_available,
            "images_available": images_available,
            "attachment_verification_status": (
                "NOT_PROVIDED"
                if not attachments_available
                else "PROVIDED_BUT_NOT_ANALYSED_IN_CURRENT_VERSION"
            ),
            "image_verification_status": (
                "NOT_PROVIDED"
                if not images_available
                else "PROVIDED_BUT_NOT_ANALYSED_IN_CURRENT_VERSION"
            ),
            "verification_note": (
                "Evidence presence is checked against provided text near the claim. "
                "External authenticity, attachments, and images are not verified "
                "unless provided and integrated."
            )
        })

    evidence_issues = [
        item for item in claim_evidence_results
        if item.get("evidence_needed")
        and item.get("evidence_status") == "MISSING_IN_TEXT"
    ]

    dependency_gaps = []

    if not attachments_available:
        dependency_gaps.append(
            "Attachment evidence not provided in current pipeline input."
        )

    if not images_available:
        dependency_gaps.append(
            "Image/media evidence not provided in current pipeline input."
        )

    dependency_gaps.append(
        "External evidence authenticity is not verified in current POC."
    )

    evidence_output = {
        "global_urls_found": global_urls,
        "global_evidence_terms_found": global_evidence_terms,
        "claim_evidence_results": claim_evidence_results,
        "evidence_issue_count": len(evidence_issues),
        "evidence_issues": evidence_issues,
        "input_coverage": input_coverage,
        "dependency_gaps": dependency_gaps
    }

    state["shared_artifacts"]["evidence_analysis"] = evidence_output

    output = {
        "module_code": "M08",
        "module_name": "Evidence Detection and Claim Matching",
        "module_status": "SUCCESS",
        "module_outcome": "EVIDENCE_MATCHING_COMPLETED",
        "evaluation_status": "PARTIAL",
        "dependency_gap": "; ".join(dependency_gaps),
        "summary": f"{len(evidence_issues)} evidence issue(s) found.",
        "data": evidence_output
    }

    logger.info("M08 completed.")
    return output