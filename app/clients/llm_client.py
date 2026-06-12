"""
Enterprise LLM Client
"""

import json
import re
import time
from typing import Dict

from openai import AzureOpenAI

from app.logger import get_logger
from config.settings import settings

logger = get_logger()

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def get_client() -> AzureOpenAI:

    return AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
    )


def is_content_filter_error(e: Exception) -> bool:
    """
    Return True when the exception was caused by Azure OpenAI's
    content safety filter (not a network / quota / parsing error).

    Azure raises openai.BadRequestError with error.code == "content_filter"
    or a ResponsibleAIPolicyViolation when the filter trips.
    We also check string patterns to catch wrapper exceptions that
    forward the original message.
    """
    err_str = str(e)
    err_lower = err_str.lower()

    return (
        "content_filter" in err_lower
        or "content filter" in err_lower
        or "ResponsibleAIPolicyViolation" in err_str
        or "responsibleaipolicyviolation" in err_lower
        # Azure sometimes returns a 400 with "harmful" in the message
        or ("400" in err_str and "harm" in err_lower)
        # openai SDK wraps the code in the string representation
        or ("'code': 'content_filter'" in err_str)
        or ('"code": "content_filter"' in err_str)
    )


def extract_json(text: str) -> Dict:

    if not text:
        raise ValueError("Empty LLM response.")

    cleaned = text.strip()

    cleaned = re.sub(
        r"^```json\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r"^```\s*",
        "",
        cleaned
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned
    )

    stripped = cleaned.rstrip()
    if stripped and stripped[-1] not in ("}", "]"):
        raise ValueError(
            f"LLM response appears truncated (ends with '...{stripped[-20:]}'). "
            f"Increase max_tokens in the policy config."
        )

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:

        match = re.search(
            r"\{.*\}",
            cleaned,
            flags=re.DOTALL
        )

        if match:
            return json.loads(match.group(0))

        raise


def call_llm_json(
    system_prompt: str,
    payload: dict,
    max_tokens: int = 2200
) -> dict:

    client = get_client()

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            logger.info(
                f"LLM call attempt "
                f"{attempt}/{MAX_RETRIES}"
            )

            response = client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,

                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            payload,
                            ensure_ascii=False,
                            default=str
                        )
                    }
                ],

                max_completion_tokens=max_tokens,

                timeout=90
            )

            content = (
                response
                .choices[0]
                .message.content
            )

            return extract_json(content)

        except Exception as e:

            last_error = e

            logger.exception(
                f"LLM call failed "
                f"(attempt {attempt}): "
                f"{str(e)}"
            )

            # Do NOT retry content filter errors — they will fail identically
            # every time. Bail out immediately so the caller can handle them
            # with a specialised fallback path.
            if is_content_filter_error(e):
                logger.warning(
                    "Content filter error detected — aborting retries immediately."
                )
                raise

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(
        f"LLM failed after "
        f"{MAX_RETRIES} attempts: "
        f"{str(last_error)}"
    )