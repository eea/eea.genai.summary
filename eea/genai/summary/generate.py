"""
Generate LLM summaries for Plone content objects using pydantic-ai agents.
"""

import logging
import re
import unicodedata

from eea.genai.core.agent import AgentDeps
from eea.genai.core.errors import AgentConfigInvalid
from eea.genai.core.settings import (
    get_agent_config,
    get_agent_for_content_type,
)
from eea.genai.core.utils import get_executor
from eea.genai.summary.image import (
    TransientImageContext,
    context_from_existing_image,
)
from eea.genai.summary.models import ImageAltResult, ImageMetadataResult
from eea.genai.summary.settings import get_image_ai_limits, require_image_ai_enabled

logger = logging.getLogger("eea.genai.summary")

#: Markers wrapping AI-generated summaries so editors can distinguish AI
#: text from human-edited text (issue #305021).
SUMMARY_MARKER_START = "[AI Generated description]"
SUMMARY_MARKER_END = "[End of AI Generated description]"


def wrap_with_ai_markers(text: str) -> str:
    """Wrap a generated summary in AI-generated markers (idempotent).

    Empty input returns empty output; already-wrapped text is returned
    unchanged.
    """
    summary = (text or "").strip()
    if not summary:
        return summary
    if summary.startswith(SUMMARY_MARKER_START):
        return summary
    return f"{SUMMARY_MARKER_START} {summary} {SUMMARY_MARKER_END}"


def _object_id(obj):
    for attr in ("getId", "absolute_url"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    return type(obj).__name__


def generate_summary_for(obj, request, properties=None):
    """Generate an LLM summary for the given object using agents.

    Uses the ``summarizer`` agent, or ``summarizer:<portal_type>`` if a
    content-type-specific agent is registered.

    ``properties`` is an optional dict of in-progress edit-form values.

    When the agent declares ``max_summary_length`` and the model
    overshoots it, the run is retried once. The retry result is adopted
    only when it is a non-empty string shorter than the first result;
    an empty or failing retry keeps the first result (the limit applies
    to the marker-free text).
    """
    content_type = obj.portal_type
    agent_name = get_agent_for_content_type("summarizer", content_type)
    if not agent_name:
        raise AgentConfigInvalid(
            f"No agent configured for content type '{content_type}'. "
            "Register an agent named 'summarizer' or "
            f"'summarizer:{content_type}' via ZCML or control panel."
        )

    agent_config = get_agent_config(agent_name) or {}
    max_length = int(agent_config.get("max_summary_length") or 0)

    def _run():
        return get_executor().run_with_agent(
            agent_name,
            deps=AgentDeps(context=obj, request=request, properties=properties),
        )

    result = _run()

    if max_length and isinstance(result, str):
        summary = result.strip()
        if len(summary) > max_length:
            logger.info(
                "LLM summary for %s is %d chars (limit %d); retrying once",
                _object_id(obj),
                len(summary),
                max_length,
            )
            try:
                retry = _run()
            except Exception:
                logger.exception(
                    "LLM summary retry failed for %s; keeping the first result",
                    _object_id(obj),
                )
            else:
                retry_text = retry.strip() if isinstance(retry, str) else ""
                if retry_text and len(retry_text) < len(summary):
                    result = retry
            if len(result.strip()) > max_length:
                logger.warning(
                    "LLM summary for %s is still %d chars after retry "
                    "(limit %d); keeping as-is",
                    _object_id(obj),
                    len(result.strip()),
                    max_length,
                )

    if agent_config.get("summary_markers") and isinstance(result, str):
        result = wrap_with_ai_markers(result)
    return {"llm_summary": result}


def _validated_result(result, model_type):
    if isinstance(result, model_type):
        return result
    return model_type.model_validate(result)


def _normalized_filename_title(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.sub(r"[\W_]+", " ", value).split())


def _title_duplicates_filename(title, filename):
    filename = str(filename or "").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    normalized_title = _normalized_filename_title(title)
    return bool(
        normalized_title
        and normalized_title
        in {
            _normalized_filename_title(filename),
            _normalized_filename_title(stem),
        }
    )


def generate_image_metadata(image, request, *, language="en"):
    """Generate validated metadata for a verified, unpersisted image.

    Retry once for an oversized result or a filename-derived title. Never
    truncate text. Both fields are regenerated together so metadata is atomic.
    """
    require_image_ai_enabled()
    title_limit, description_limit = get_image_ai_limits()
    context = TransientImageContext(image=image, language=language)
    executor = get_executor()
    retry_instruction = ""
    for attempt in range(2):
        result = executor.run_with_agent(
            "image_metadata",
            user_prompt=(
                f"Output language code: {language}. Title: at most {title_limit} "
                f"characters. Description: at most {description_limit} characters."
                f"{retry_instruction}"
            ),
            deps=AgentDeps(context=context, request=request),
        )
        validated = _validated_result(result, ImageMetadataResult)
        if (
            len(validated.title) > title_limit
            or len(validated.description) > description_limit
        ):
            retry_instruction = (
                " The previous result exceeded the character limits; shorten it "
                "while preserving factual content and complete sentences."
            )
        elif _title_duplicates_filename(validated.title, image.filename):
            retry_instruction = (
                " The previous title duplicated the upload filename; replace it "
                "with a factual phrase based only on visible content."
            )
        else:
            return validated.model_dump()
    raise ValueError("Image metadata remains invalid after one retry")


def generate_image_alt(context, request, *, language="en"):
    """Generate a bounded alt suggestion, retrying once without truncation."""
    require_image_ai_enabled()
    alt_limit, _ = get_image_ai_limits()
    transient_context = context_from_existing_image(context)
    transient_context.language = language
    executor = get_executor()
    for attempt in range(2):
        retry_instruction = (
            " The previous alt exceeded the character limit; shorten it while "
            "preserving factual content and a complete sentence."
            if attempt
            else ""
        )
        result = executor.run_with_agent(
            "image_alt",
            user_prompt=(
                f"Output language code: {language}. Alt: at most {alt_limit} "
                f"characters.{retry_instruction}"
            ),
            deps=AgentDeps(context=transient_context, request=request),
        )
        validated = _validated_result(result, ImageAltResult)
        if len(validated.alt) <= alt_limit:
            return validated.model_dump()
    raise ValueError("Image alt exceeds its character limit after one retry")
