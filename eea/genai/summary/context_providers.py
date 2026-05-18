"""Agent skills for eea.genai.summary."""

from plone.restapi.deserializer import json_body

from eea.genai.core.interfaces import AgentContextProvider


class _Source:
    """Unified accessor: properties dict overrides context attributes."""

    def __init__(self, context, properties):
        self._context = context
        self._properties = properties

    def __getattr__(self, name):
        if name in self._properties:
            return self._properties[name]
        return getattr(self._context, name, None)


class GenericMetadataProvider(AgentContextProvider):
    """Extracts content metadata and adds it to the user prompt.

    Pulls title, description, language, geographic coverage, and temporal
    coverage from the content object (via deps.context).

    The prior llm_summary is intentionally NOT injected by default. Feeding
    the previous summary back into the prompt of a regeneration causes
    drift and corrupts RAG embeddings. Opt in via the `include_llm_summary`
    flag (e.g. for chat/enrichment agents that genuinely want it).
    """

    name = "generic_metadata"
    description = "Adds content metadata (title, description, language, geo/temporal coverage) to the user prompt"
    include_llm_summary = False

    def user_prompt(self, deps):
        context = getattr(deps, "context", None)
        properties = getattr(deps, "properties", None) or {}
        request = getattr(deps, "request", None)
        payload = json_body(request)
        if context is None:
            return ""
        source = _Source(context, properties)

        include_llm_summary = self.include_llm_summary
        if payload and "include_prior_summary" in payload:
            include_llm_summary = True

        parts = extract_metadata_prompt(source, include_llm_summary=include_llm_summary)
        return "### Generic page metadata\n\n" + "\n".join(parts) if parts else ""


def extract_metadata_prompt(context, include_llm_summary=False):
    """Extract common EEA metadata fields from a content object.

    Returns a list of formatted strings like ["Title: ...", "Description: ..."].
    Suitable for inclusion in an LLM user prompt.

    When include_llm_summary is False (default) the prior llm_summary is
    omitted to avoid self-reference drift during regeneration.
    """
    parts = []

    title = getattr(context, "title", "") or ""
    if title:
        parts.append(f"Title: {title}")

    description = getattr(context, "description", "") or ""
    if description:
        parts.append(f"Description: {description}")

    language = getattr(context, "language", None)
    if language:
        lang_code = getattr(language, "token", None) or language
        parts.append(f"Language: {lang_code}")

    geo_coverage = getattr(context, "geo_coverage", None)
    if geo_coverage and isinstance(geo_coverage, dict):
        group = geo_coverage.get("selectedGroup") or {}
        locations = geo_coverage.get("geolocation") or []
        labels = [loc["label"] for loc in locations if loc.get("label")]
        if group.get("label"):
            parts.append(f"Geographic coverage: {group['label']} ({', '.join(labels)})")
        elif labels:
            parts.append(f"Geographic coverage: {', '.join(labels)}")
    elif geo_coverage:
        parts.append(f"Geographic coverage: {geo_coverage}")

    temporal_coverage = getattr(context, "temporal_coverage", None)
    if temporal_coverage:
        if isinstance(temporal_coverage, (list, tuple)):
            parts.append(
                f"Temporal coverage: {', '.join(str(t) for t in temporal_coverage)}"
            )
        else:
            parts.append(f"Temporal coverage: {temporal_coverage}")

    if include_llm_summary:
        llm_summary = getattr(context, "llm_summary", None)
        if llm_summary:
            parts.append(f"LLM summary: {llm_summary}")

    return parts
