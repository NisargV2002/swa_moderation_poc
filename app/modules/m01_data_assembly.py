"""
M01: Client Data Assembly

Purpose:
- Collect and organize moderation input safely.
- Build clean field-level text map.
- Preserve traceability between fields and extracted claims.
- Detect available input coverage.

Important:
- M01 does NOT perform moderation logic.
- M01 prepares structured moderation input for downstream modules.
- All later modules depend on this stage being reliable.
"""

from app.logger import get_logger

logger = get_logger()


def detect_input_coverage(project: dict) -> dict:
    """
    Detects what input types are available.

    Important:
    Never pretend attachments/images were analysed if they were not provided.
    """

    attachment_fields = [
        "AttachmentPath",
        "AttachmentUrl",
        "AttachmentUrls",
        "ImagePath",
        "ImageUrl",
        "ImageUrls",
        "DocumentPath",
        "DocumentUrl"
    ]

    found_attachment_fields = {
        field: project.get(field)
        for field in attachment_fields
        if project.get(field)
    }

    return {
        "text_fields_available": True,

        "attachments_available": bool(
            found_attachment_fields
        ),

        "attachment_fields_found": found_attachment_fields,

        "images_available": any(
            key.lower().startswith("image")
            for key in found_attachment_fields.keys()
        ),

        "coverage_note": (
            "Current pipeline analyses provided text fields. "
            "Attachments/images are only analysed if paths/URLs "
            "are present in input."
        )
    }


def build_field_text_map(
    project: dict,
    fields_to_scan: list
) -> dict:
    """
    Creates field -> text mapping.

    Only meaningful non-empty text is included.
    """

    field_text_map = {}

    for field_name in fields_to_scan:
        value = project.get(field_name)

        if value is not None:
            clean = str(value).strip()

            if clean:
                field_text_map[field_name] = clean

    return field_text_map


def build_context_map(
    project: dict,
    context_fields: list
) -> dict:
    """
    Builds non-primary contextual metadata.

    Context helps moderation reasoning
    but is not scanned as primary moderation text.
    """

    context_map = {}

    for field_name in context_fields:
        value = project.get(field_name)

        if value is not None:
            clean = str(value).strip()

            if clean:
                context_map[field_name] = value

    return context_map


def build_combined_text(field_text_map: dict) -> str:
    """
    Creates readable combined moderation text.

    Field names are preserved for traceability.
    """

    return "\n\n".join(
        f"{field_name}: {text}"
        for field_name, text in field_text_map.items()
    )


def run_m01_data_assembly(
    state: dict,
    policy_config: dict
) -> dict:
    """
    Main M01 runner.

    Produces:
    - field_text_map
    - context_map
    - combined_text
    - input_coverage
    """

    logger.info("M01 started: Client Data Assembly.")

    project = state["project"]

    fields_to_scan = policy_config.get(
        "fields_to_scan",
        []
    )

    context_fields = policy_config.get(
        "context_fields",
        []
    )

    field_text_map = build_field_text_map(
        project,
        fields_to_scan
    )

    context_map = build_context_map(
        project,
        context_fields
    )

    combined_text = build_combined_text(
        field_text_map
    )

    input_coverage = detect_input_coverage(
        project
    )

    state["shared_artifacts"][
        "field_text_map"
    ] = field_text_map

    state["shared_artifacts"][
        "context_map"
    ] = context_map

    state["shared_artifacts"][
        "combined_text"
    ] = combined_text

    state["shared_artifacts"][
        "input_coverage"
    ] = input_coverage

    output = {
        "module_code": "M01",
        "module_name": "Client Data Assembly",
        "module_status": "SUCCESS",
        "module_outcome": "INPUT_PREPARED",
        "evaluation_status": "FULL",
        "dependency_gap": None,

        "summary": (
            f"Prepared moderation input using "
            f"{len(field_text_map)} text field(s)."
        ),

        "data": {
            "policy_code": policy_config.get(
                "policy_code"
            ),

            "fields_requested": fields_to_scan,

            "fields_used": list(
                field_text_map.keys()
            ),

            "context_fields_used": list(
                context_map.keys()
            ),

            "field_text_map": field_text_map,

            "context_map": context_map,

            "combined_text": combined_text,

            "input_coverage": input_coverage
        }
    }

    logger.info("M01 completed.")
    return output