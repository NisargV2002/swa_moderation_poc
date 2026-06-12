"""
M05: Entity Hint Extraction

Purpose:
- Extract lightweight deterministic entity hints.
- Support downstream moderation reasoning.
- Help identify authority references, organisations, partnerships, certifications.

Important:
- This module is NOT the main semantic understanding engine.
- M07 LLM performs deep semantic claim/entity reasoning.
- M05 only provides support signals and traceable hints.

Why this exists:
- Some exact entity patterns are useful for:
    - authority affiliation detection
    - partnership detection
    - certification references
    - government references
- These deterministic hints improve explainability and auditability.
"""

import re

from app.logger import get_logger

logger = get_logger()


ENTITY_PATTERNS = [
    r"\bUnited Nations\b",
    r"\bWorld Bank\b",
    r"\bGovernment\b",
    r"\bMinistry\b",
    r"\bCouncil\b",
    r"\bUniversity\b",
    r"\bFoundation\b",
    r"\bAgency\b",
    r"\bAlliance\b",
    r"\bDepartment\b",
    r"\bAuthority\b",
    r"\bRegulator\b",
    r"\bNGO\b",
]


def extract_authority_entities(text: str) -> list:
    """
    Extract authority-related entity mentions.

    These are deterministic support signals only.
    """

    matches = []

    for pattern in ENTITY_PATTERNS:
        found = re.findall(pattern, text, flags=re.IGNORECASE)

        for item in found:
            matches.append(item.strip())

    return sorted(set(matches))


def extract_proper_noun_phrases(text: str) -> list:
    """
    Extract simple proper noun phrase hints.

    Example:
    - Green Adelaide Initiative
    - Climate Research Foundation

    This is intentionally lightweight for POC.
    """

    phrases = re.findall(
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\b",
        text
    )

    return sorted(set(phrases[:30]))


def build_entity_summary(entities: dict) -> dict:
    """
    Create lightweight analytics summary for explainability.
    """

    return {
        "authority_entity_count": len(
            entities.get("authority_or_org_terms", [])
        ),
        "proper_noun_phrase_count": len(
            entities.get("proper_noun_phrase_hints", [])
        ),
        "has_authority_reference": (
            len(entities.get("authority_or_org_terms", [])) > 0
        ),
        "entity_extraction_scope": (
            "Deterministic support extraction only. "
            "LLM performs semantic entity reasoning separately."
        )
    }


def run_m05_entity_extraction(state: dict, policy_config: dict) -> dict:
    """
    Main M05 runner.

    Extracts:
    - authority/entity hints
    - proper noun phrase hints
    - sponsor identity context
    """

    logger.info("M05 started: Entity Hint Extraction.")

    normalized_text = state["shared_artifacts"].get(
        "normalized_text",
        ""
    )

    context_map = state["shared_artifacts"].get(
        "context_map",
        {}
    )

    sponsor_name = " ".join(
        str(x).strip()
        for x in [
            context_map.get("ProjectSponsorFirstName"),
            context_map.get("ProjectSponsorLastName")
        ]
        if x
    )

    authority_entities = extract_authority_entities(
        normalized_text
    )

    proper_noun_phrases = extract_proper_noun_phrases(
        normalized_text
    )

    entities = {
        "sponsor_name_from_context": sponsor_name or None,
        "authority_or_org_terms": authority_entities,
        "proper_noun_phrase_hints": proper_noun_phrases,
        "ner_status": "LIGHTWEIGHT_RULE_SUPPORT_ONLY",
        "ner_upgrade_note": (
            "Future versions may integrate Azure AI Language NER "
            "or LLM-native semantic entity extraction."
        )
    }

    entities["entity_summary"] = build_entity_summary(
        entities
    )

    state["shared_artifacts"]["entities"] = entities

    output = {
        "module_code": "M05",
        "module_name": "Entity Hint Extraction",
        "module_status": "SUCCESS",
        "module_outcome": "ENTITY_HINTS_EXTRACTED",
        "evaluation_status": "PARTIAL",
        "dependency_gap": (
            "Full external entity verification is not performed."
        ),
        "summary": (
            f"Extracted "
            f"{len(authority_entities)} authority/entity hint(s) "
            f"and "
            f"{len(proper_noun_phrases)} proper noun phrase hint(s)."
        ),
        "data": entities
    }

    logger.info("M05 completed.")
    return output