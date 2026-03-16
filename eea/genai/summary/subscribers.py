"""Event subscribers for automatic LLM summary generation using agents."""

import logging

from zope.component import queryUtility
from zope.globalrequest import getRequest

from eea.genai.core.interfaces import IAgentExecutor
from eea.genai.core.settings import get_agent_for_content_type
from eea.genai.core.agent import AgentDeps

logger = logging.getLogger("eea.genai.summary")


def generate_summary_for(obj, request):
    """Generate an LLM summary for the given object using agents.

    Uses the ``summarizer`` agent, or ``summarizer:<portal_type>`` if a
    content-type-specific agent is registered.

    Raises RuntimeError if no agent is configured or if execution fails.
    """
    content_type = obj.portal_type
    agent_name = get_agent_for_content_type('summarizer', content_type)

    if not agent_name:
        raise RuntimeError(
            f"No agent configured for content type '{content_type}'. "
            "Register an agent named 'summarizer' or "
            f"'summarizer:{content_type}' via ZCML or control panel."
        )

    executor = queryUtility(IAgentExecutor)
    if executor is None:
        raise RuntimeError("No IAgentExecutor utility registered")

    # Create agent deps with context
    deps = AgentDeps(context=obj, request=request)

    # Skills handle prompt enrichment (metadata, blocks text, etc.)
    result = executor.run_with_agent(agent_name, deps=deps)

    # Store result
    obj.llm_summary = result
    obj.reindexObject(idxs=["modified"])

    return {"llm_summary": result}


def on_content_modified(obj, event):
    """Auto-generate summary on save if allow_llm_summary is True."""
    allow = getattr(obj, "allow_llm_summary", False)
    if not allow:
        return

    request = getRequest()
    try:
        generate_summary_for(obj, request)
    except Exception as e:
        logger.warning(
            "LLM summary generation failed for %s: %s",
            obj.absolute_url(),
            str(e),
        )
