"""Agent configurations for summarizing Plone content."""

from eea.genai.core.interfaces import AgentConfiguration


SYSTEM_PROMPT = """\
You are an expert content analyst. You will receive information about a \
piece of content published in Plone CMS.
Do not use bullet points or markdown. Write in a clear, informative style \
suitable for screen readers and general audiences.
If you are unable to resolve the task answer with empty string.
"""

TASK_PROMPT = """\
Produce a 3-8 sentence plain prose summary that captures the key information, \
purpose, and scope of the content.
"""


class SummarizerAgent(AgentConfiguration):
    """Content summarizer agent for the Plone website."""
    system_prompt = SYSTEM_PROMPT
    task_prompt = TASK_PROMPT
    context_providers = ["generic_metadata", "blocks"]
