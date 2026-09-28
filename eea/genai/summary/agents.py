"""Agent configurations for summarizing Plone content."""

from eea.genai.core.interfaces import AgentConfiguration


SYSTEM_PROMPT = """\
You are an expert content analyst. You will receive information about a \
piece of content published in Plone CMS.
Do not use bullet points or markdown. Write in a clear, informative style \
suitable for screen readers and general audiences.
If you are unable to resolve the task answer with empty string."""

TASK_PROMPT = """\
Produce a 3-8 sentence plain prose summary that captures the key information, \
purpose, and scope of the content."""


class SummarizerAgent(AgentConfiguration):
    """Content summarizer agent for the Plone website."""

    system_prompt = SYSTEM_PROMPT
    task_prompt = TASK_PROMPT
    context_providers = ["generic_metadata", "blocks"]


IMAGE_SYSTEM_PROMPT = """\
You are an expert at writing concise, factual image alt text.
Rules:
- Describe only the most important visible subject, action, setting,
  and any essential readable text.
- Do not infer identity, intent, emotion, or facts that are not visible.
- Write in plain prose. No bullet points, no markdown, no labels or \
prefixes.
- Do not begin with "This image" or "Image of".
- Do not add AI markers or disclaimers to your answer.
- Match the language of the content metadata when provided."""

IMAGE_TASK_PROMPT = """\
Write an alt-text style description of the attached image as exactly one \
sentence, no more than 125 characters (including spaces), clearly stating \
what is visible in the image."""


class ImageSummarizerAgent(AgentConfiguration):
    """Content-type-specific multimodal summarizer for Image objects.

    The ``image_content`` enricher attaches the actual image bytes to the
    prompt, so the description reflects what is visible in the image, not
    just the metadata. The summary is a single short alt-text-style
    sentence (``max_summary_length`` chars); ``generate_summary_for``
    retries once when the model overshoots the limit. The generated summary
    is wrapped in AI-generated markers (see
    ``generate.wrap_with_ai_markers``) so editors can tell AI text from
    human text.
    """

    name = "summarizer:Image"
    system_prompt = IMAGE_SYSTEM_PROMPT
    task_prompt = IMAGE_TASK_PROMPT
    enrichers = ["generic_metadata_no_dates", "image_content"]
    summary_markers = True
    #: Max length in characters for the generated alt text (markers not
    #: counted); a single retry is attempted when the model overshoots.
    max_summary_length = 125
