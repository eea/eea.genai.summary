"""Event subscribers for automatic LLM summary generation using agents."""

import logging

from zope.globalrequest import getRequest

from eea.genai.core.agent import AgentDeps as CoreAgentDeps
from eea.genai.summary.generate import generate_summary_for

logger = logging.getLogger("eea.genai.summary")


class AgentDeps(CoreAgentDeps):
    """Dependencies passed to agent tools via RunContext.

    This class is passed as `deps` to the pydantic_ai Agent,
    making it available in tool functions via `ctx.deps`.
    """

    def __init__(self, context=None, request=None, properties=None):
        super().__init__(context=context, request=request)
        self.properties = properties


def on_content_modified(obj, event):
    """Auto-generate summary on save only when the field is still empty.

    Rationale: regenerating on every save clobbers editor-authored
    summaries and burns LLM budget on trivial metadata edits. Explicit
    regeneration is handled by the @llm-summary REST endpoint (driven by
    the frontend widget's "Regenerate" button) and by the
    @llm-summary-batch / @visualizations-summarize bulk endpoints.
    """
    if not getattr(obj, "allow_llm_summary", False):
        return

    existing = getattr(obj, "llm_summary", None)
    if existing and existing.strip():
        return

    request = getRequest()
    try:
        result = generate_summary_for(obj, request)
        if not result:
            return
        summary = result.get("llm_summary")
        # Preserve prior summary if the agent returned empty/whitespace.
        # An empty result usually means the agent could not produce a valid
        # summary (insufficient context, malformed visualization, etc.) — we
        # would rather keep what we have than wipe the field.
        if summary and summary.strip():
            obj.llm_summary = summary
            obj.reindexObject(idxs=["modified"])
    except Exception as e:
        logger.warning(
            "LLM summary generation failed for %s: %s",
            obj.absolute_url(),
            str(e),
        )
