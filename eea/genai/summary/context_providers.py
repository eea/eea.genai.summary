"""Agent skills for eea.genai.summary."""

from eea.genai.core.interfaces import AgentContextProvider


class GenericMetadataProvider(AgentContextProvider):
    """Extracts content metadata and adds it to the user prompt.

    Pulls title, description, geographic coverage, and temporal coverage
    from the content object (via deps.context).
    """

    name = "generic_metadata"
    description = "Adds content metadata (title, description, geo/temporal coverage) to the user prompt"

    def user_prompt(self, deps):
        context = getattr(deps, "context", None)
        if context is None:
            return ""
        parts = extract_metadata_prompt(context)
        return "### Generic page metadata\n\n" + "\n".join(parts) if parts else ""


def extract_metadata_prompt(context):
    """Extract common EEA metadata fields from a content object.

    Returns a list of formatted strings like ["Title: ...", "Description: ..."].
    Suitable for inclusion in an LLM user prompt.
    """
    parts = []

    title = getattr(context, "title", "") or ""
    if title:
        parts.append(f"Title: {title}")

    description = getattr(context, "description", "") or ""
    if description:
        parts.append(f"Description: {description}")

    geo_coverage = getattr(context, "geo_coverage", None)
    if geo_coverage and isinstance(geo_coverage, dict):
        group = geo_coverage.get("selectedGroup") or {}
        locations = geo_coverage.get("geolocation") or []
        labels = [loc["label"] for loc in locations if loc.get("label")]
        if group.get("label"):
            parts.append(
                f"Geographic coverage: {group['label']} ({', '.join(labels)})"
            )
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

    llm_summary = getattr(context, "llm_summary", None)

    if llm_summary:
        parts.append(f"LLM summary: {llm_summary}")

    return parts
