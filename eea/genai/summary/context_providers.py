"""Agent skills for eea.genai.summary."""

from plone.restapi.deserializer import json_body

from eea.genai.core.interfaces import Enricher
from eea.genai.core.utils import Source


class GenericMetadataProvider(Enricher):
    """Extracts content metadata and adds it to the user prompt.

    Pulls title, description, language, geographic coverage, and temporal
    coverage from the content object (via deps.context).

    Enricher-level flags (override on subclasses for per-agent variants):

    - ``include_llm_summary``: include the prior llm_summary in the prompt.
      Off by default — feeding a previous summary back into a regeneration
      causes drift and corrupts RAG embeddings. Turn on for chat/enrichment
      agents that genuinely want it.
    - ``include_temporal_coverage``: include the temporal coverage field
      (years list). Off in subclasses used by quantitative-leak-sensitive
      agents (e.g. chart summarizer that must not mention numbers or year
      ranges).
    - ``include_geo_coverage``: include geographic coverage labels.
    """

    name = "generic_metadata"
    description = "Adds content metadata (title, description, language, geo/temporal coverage) to the user prompt"
    include_llm_summary = False
    include_temporal_coverage = True
    include_geo_coverage = True

    def user_prompt(self, deps):
        context = getattr(deps, "context", None)
        properties = getattr(deps, "properties", None) or {}
        request = getattr(deps, "request", None)
        payload = json_body(request)
        if context is None:
            return ""
        source = Source(context, properties)

        include_llm_summary = self.include_llm_summary
        if payload and "include_prior_summary" in payload:
            include_llm_summary = True

        parts = extract_metadata_prompt(
            source,
            include_llm_summary=include_llm_summary,
            include_temporal_coverage=self.include_temporal_coverage,
            include_geo_coverage=self.include_geo_coverage,
        )
        return "### Generic page metadata\n\n" + "\n".join(parts) if parts else ""


class GenericMetadataNoDatesProvider(GenericMetadataProvider):
    """Variant of generic_metadata that omits temporal coverage.

    Use on agents that must not leak years, year ranges, or any
    quantitative date information (e.g. chart summarizer). Registered
    as the named utility ``generic_metadata_no_dates``.
    """

    name = "generic_metadata_no_dates"
    description = (
        "Adds content metadata (title, description, language, geo coverage) "
        "to the user prompt. Omits temporal coverage to prevent year leakage."
    )
    include_temporal_coverage = False


def extract_metadata_prompt(
    context,
    include_llm_summary=False,
    include_temporal_coverage=True,
    include_geo_coverage=True,
):
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

    if include_geo_coverage:
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

    if include_temporal_coverage:
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
