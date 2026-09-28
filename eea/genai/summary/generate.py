"""
Generate LLM summaries for Plone content objects using pydantic-ai agents.
"""

import logging

from eea.genai.core.agent import AgentDeps
from eea.genai.core.errors import AgentConfigInvalid
from eea.genai.core.settings import (
    get_agent_config,
    get_agent_for_content_type,
)
from eea.genai.core.utils import get_executor

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
