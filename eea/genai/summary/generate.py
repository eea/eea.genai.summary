"""
Generate LLM summaries for Plone content objects using pydantic-ai agents.
"""

import logging

from zope.component import queryUtility

from eea.genai.core.agent import AgentDeps as CoreAgentDeps
from eea.genai.core.interfaces import IAgentExecutor
from eea.genai.core.settings import get_agent_for_content_type

logger = logging.getLogger("eea.genai.summary")


class AgentDeps(CoreAgentDeps):
    """Dependencies passed to agent tools via RunContext.

    This class is passed as `deps` to the pydantic_ai Agent,
    making it available in tool functions via `ctx.deps`.
    """

    def __init__(self, context=None, request=None, properties=None):
        super().__init__(context=context, request=request)
        self.properties = properties


def generate_summary_for(obj, request, properties=None):
    """Generate an LLM summary for the given object using agents.

    Uses the ``summarizer`` agent, or ``summarizer:<portal_type>`` if a
    content-type-specific agent is registered.

    ``properties`` is an optional dict of in-progress edit-form values.
    When provided, context providers consult it (via the ``_Source``
    accessor in context_providers) so that unsaved changes are reflected
    in the generated summary instead of the persisted object state.

    Raises RuntimeError if no agent is configured or if execution fails.
    """
    content_type = obj.portal_type
    agent_name = get_agent_for_content_type("summarizer", content_type)

    if not agent_name:
        raise RuntimeError(
            f"No agent configured for content type '{content_type}'. "
            "Register an agent named 'summarizer' or "
            f"'summarizer:{content_type}' via ZCML or control panel."
        )

    executor = queryUtility(IAgentExecutor)
    if executor is None:
        raise RuntimeError("No IAgentExecutor utility registered")

    # Skills handle prompt enrichment (metadata, blocks text, etc.)
    result = executor.run_with_agent(
        agent_name,
        deps=AgentDeps(context=obj, request=request, properties=properties),
    )

    return {"llm_summary": result}
