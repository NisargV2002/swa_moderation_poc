"""
M02: Language Detection, Text Normalization, and Span Mapping

Purpose:
- Normalize project text safely.
- Detect the real language from text using langdetect.
- Do NOT depend on DB LanguageCode.
- Preserve LanguageCode only as optional synthetic/test metadata.
- Create traceable spans for downstream modules.

Why this is important:
- SWA project content can be multilingual.
- Rule/keyword logic is language-sensitive.
- LLM prompts need language context.
- Moderation must not silently PASS content just because English rules missed it.
"""

import re
from langdetect import detect_langs, DetectorFactory, LangDetectException

from app.logger import get_logger

logger = get_logger()

# Makes langdetect deterministic across runs.
DetectorFactory.seed = 0


def normalize_whitespace(text: str) -> str:
    """
    Normalize only whitespace.

    We do NOT lowercase everything because:
    - evidence excerpts should stay human-readable
    - original casing may matter for names/entities
    """

    if not text:
        return ""

    return re.sub(r"\s+", " ", str(text)).strip()


def detect_language_from_text(text: str) -> dict:
    """
    Detects actual language using langdetect.

    Returns:
    - detected_language: ISO code like en, es, fr, hi
    - language_confidence: approximate probability from langdetect
    - translation_required: True if not English
    - language_detection_method
    """

    clean_text = normalize_whitespace(text)

    if not clean_text:
        return {
            "detected_language": "unknown",
            "language_confidence": 0.0,
            "language_detection_method": "empty_text",
            "translation_required": False,
            "language_candidates": [],
            "language_detection_notes": "No text available for detection."
        }

    try:
        candidates = detect_langs(clean_text)

        if not candidates:
            return {
                "detected_language": "unknown",
                "language_confidence": 0.0,
                "language_detection_method": "langdetect_no_candidates",
                "translation_required": False,
                "language_candidates": [],
                "language_detection_notes": "langdetect returned no candidates."
            }

        top = candidates[0]
        detected_lang = top.lang
        confidence = float(top.prob)

        return {
            "detected_language": detected_lang,
            "language_confidence": round(confidence, 3),
            "language_detection_method": "langdetect",
            "translation_required": detected_lang != "en",
            "language_candidates": [
                {
                    "language": candidate.lang,
                    "confidence": round(float(candidate.prob), 3)
                }
                for candidate in candidates[:3]
            ],
            "language_detection_notes": (
                "Detected from actual project text. "
                "DB LanguageCode is not required."
            )
        }

    except LangDetectException as e:
        logger.warning(f"Language detection failed: {str(e)}")

        return {
            "detected_language": "unknown",
            "language_confidence": 0.0,
            "language_detection_method": "langdetect_failed",
            "translation_required": False,
            "language_candidates": [],
            "language_detection_notes": str(e)
        }


def create_spans(field_text_map: dict) -> list:
    """
    Creates traceable text spans.

    Every span keeps:
    - span_id
    - field_name
    - original_text
    - normalized_text

    This allows later evidence to say:
    "This claim came from ProjectDescription, span 2."
    """

    spans = []
    span_id = 1

    for field_name, text in field_text_map.items():
        field_text = normalize_whitespace(text)

        # Simple sentence split for POC.
        # Later this can be replaced with a stronger sentence segmenter.
        parts = re.split(r"(?<=[.!?])\s+", field_text)

        for part in parts:
            clean = normalize_whitespace(part)

            if clean:
                spans.append({
                    "span_id": span_id,
                    "field_name": field_name,
                    "original_text": clean,
                    "normalized_text": clean
                })
                span_id += 1

    return spans


def run_m02_language_and_spans(state: dict, policy_config: dict) -> dict:
    """
    Main M02 runner.

    Inputs from M01:
    - field_text_map
    - context_map
    - combined_text

    Outputs to shared_artifacts:
    - normalized_text
    - sentence_spans
    - language_info
    """

    logger.info("M02 started: Language Detection and Span Mapping.")

    field_text_map = state["shared_artifacts"].get("field_text_map", {})
    context_map = state["shared_artifacts"].get("context_map", {})

    combined_original_text = "\n\n".join(
        f"{field_name}: {text}"
        for field_name, text in field_text_map.items()
    )

    normalized_text = normalize_whitespace(combined_original_text)
    spans = create_spans(field_text_map)

    language_info = detect_language_from_text(normalized_text)

    provided_language_hint = context_map.get("LanguageCode")

    language_info["provided_language_hint"] = provided_language_hint
    language_info["provided_language_hint_note"] = (
        "Optional synthetic/test metadata only. "
        "Actual client DB may not have this field, so the pipeline uses text detection."
    )

    # Test sanity check only:
    # If synthetic LanguageCode exists and differs from detected language,
    # record it for debugging, but do not depend on it as the real source.
    if provided_language_hint:
        language_info["language_hint_matches_detection"] = (
            str(provided_language_hint).lower()
            == str(language_info.get("detected_language")).lower()
        )

    state["shared_artifacts"]["normalized_text"] = normalized_text
    state["shared_artifacts"]["sentence_spans"] = spans
    state["shared_artifacts"]["language_info"] = language_info

    evaluation_status = "FULL"
    dependency_gap = None

    if language_info.get("detected_language") == "unknown":
        evaluation_status = "PARTIAL"
        dependency_gap = "Language could not be detected confidently."

    output = {
        "module_code": "M02",
        "module_name": "Language Detection and Span Mapping",
        "module_status": "SUCCESS",
        "module_outcome": "LANGUAGE_AND_SPANS_READY",
        "evaluation_status": evaluation_status,
        "dependency_gap": dependency_gap,
        "summary": (
            f"Detected language '{language_info.get('detected_language')}' "
            f"with confidence {language_info.get('language_confidence')}; "
            f"created {len(spans)} traceable span(s)."
        ),
        "data": {
            "normalized_text_length": len(normalized_text),
            "span_count": len(spans),
            "language_info": language_info,
            "sentence_spans": spans
        }
    }

    logger.info("M02 completed.")
    return output