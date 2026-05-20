"""
Generate LLM summaries for Plone content objects using pydantic-ai agents.
"""

import logging

from eea.genai.core.agent import AgentDeps
from eea.genai.core.errors import AgentConfigInvalid
from eea.genai.core.settings import get_agent_for_content_type
from eea.genai.core.utils import get_executor

logger = logging.getLogger("eea.genai.summary")


def generate_summary_for(obj, request, properties=None):
    """Generate an LLM summary for the given object using agents.

    Uses the ``summarizer`` agent, or ``summarizer:<portal_type>`` if a
    content-type-specific agent is registered.

    ``properties`` is an optional dict of in-progress edit-form values.
    """
    content_type = obj.portal_type
    agent_name = get_agent_for_content_type("summarizer", content_type)
    if not agent_name:
        raise AgentConfigInvalid(
            f"No agent configured for content type '{content_type}'. "
            "Register an agent named 'summarizer' or "
            f"'summarizer:{content_type}' via ZCML or control panel."
        )

    result = get_executor().run_with_agent(
        agent_name,
        deps=AgentDeps(context=obj, request=request, properties=properties),
    )
    return {"llm_summary": result}
