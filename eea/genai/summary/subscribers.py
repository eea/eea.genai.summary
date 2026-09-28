"""Event subscribers for automatic LLM summary generation using agents."""

import logging

from zope.globalrequest import getRequest

from eea.genai.core.agent import AgentDeps as CoreAgentDeps
from eea.genai.summary.catalog import ensure_llm_summary_catalog_column
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
            ensure_llm_summary_catalog_column(obj)
            obj.reindexObject(idxs=["modified"])
    except Exception as e:
        logger.warning(
            "LLM summary generation failed for %s: %s",
            obj.absolute_url(),
            str(e),
        )


def on_content_created(obj, event):
    """Auto-generate summary at creation time — Image content only.

    The REST/Volto upload path fires ObjectCreatedEvent (not
    ObjectModifiedEvent), so an uploaded image would never be summarized
    without this subscriber. Generation is gated on the object carrying
    actual image data at creation: other ILLMSummary content types are
    expected to be created empty and filled in later, and their first
    save (IObjectModifiedEvent) triggers generation instead. Generating
    at create time for an empty object would burn an LLM call on
    metadata only and then suppress the later, meaningful generation.
    """
    image = getattr(obj, "image", None)
    if image is None:
        return
    size_fn = getattr(image, "getSize", None)
    if callable(size_fn):
        try:
            if not size_fn():
                return
        except Exception:
            return
    else:
        # No cheap size accessor (e.g. test doubles) — fall back to a data
        # check so the gate stays meaningful.
        if getattr(image, "data", None) is None:
            return
    on_content_modified(obj, event)
