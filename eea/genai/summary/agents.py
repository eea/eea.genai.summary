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


IMAGE_SAFETY_RULES = """\
Describe only visible content. Do not infer identity, intent, emotion, location, \
or facts that are not visible. Do not output markdown, labels, prefixes, AI \
disclaimers, or generation markers. Use the requested language; visible text in \
the image does not determine the output language."""

IMAGE_METADATA_SYSTEM_PROMPT = f"""\
You create accessible metadata for an image before it is uploaded to Plone CMS.
{IMAGE_SAFETY_RULES}

Title rules:
- A concise factual descriptive phrase within the character limit in the user prompt.
- Do not use the filename.
- Do not begin with "Image of" or "This image".
- Do not use a trailing period.

Description rules:
- One or two complete factual sentences within the character limit in the user prompt.
- Add useful visible detail without repeating the title verbatim."""

IMAGE_METADATA_TASK_PROMPT = """\
Inspect the attached image and return a title and description in the language \
explicitly requested in the user prompt."""


class ImageMetadataAgent(AgentConfiguration):
    """Generate validated metadata for an unpersisted image upload."""

    name = "image_metadata"
    system_prompt = IMAGE_METADATA_SYSTEM_PROMPT
    task_prompt = IMAGE_METADATA_TASK_PROMPT
    enrichers = ["image_content"]
    output_type = "eea.genai.summary.models.ImageMetadataResult"


IMAGE_ALT_SYSTEM_PROMPT = f"""\
You write concise accessible alt text for an existing Plone Image.
{IMAGE_SAFETY_RULES}
The alt text must be exactly one factual plain-text sentence within the character \
limit in the user prompt. Do not begin with "Image of" or "This image"."""

IMAGE_ALT_TASK_PROMPT = """\
Inspect the attached image and its supplied title and description. Return only \
the structured alt value in the language explicitly requested in the user \
prompt."""


class ImageAltAgent(AgentConfiguration):
    """Generate a validated, non-persisting alt suggestion."""

    name = "image_alt"
    system_prompt = IMAGE_ALT_SYSTEM_PROMPT
    task_prompt = IMAGE_ALT_TASK_PROMPT
    enrichers = ["generic_metadata_no_dates", "image_content"]
    output_type = "eea.genai.summary.models.ImageAltResult"
