"""Unit tests for context_providers.extract_metadata_prompt and agent configs.

Pure-function tests — no Plone bootstrap required.
"""

import unittest
from types import SimpleNamespace

from eea.genai.summary.context_providers import (
    GenericMetadataNoDatesProvider,
    GenericMetadataProvider,
    extract_metadata_prompt,
)
from eea.genai.summary.agents import SummarizerAgent


class TestExtractMetadataPrompt(unittest.TestCase):
    def _ctx(self, **kwargs):
        return SimpleNamespace(**kwargs)

    def test_empty_context_returns_empty_list(self):
        self.assertEqual(extract_metadata_prompt(self._ctx()), [])

    def test_title_included(self):
        result = extract_metadata_prompt(self._ctx(title="My Report"))
        self.assertIn("Title: My Report", result)

    def test_empty_title_not_included(self):
        result = extract_metadata_prompt(self._ctx(title="", description="Desc"))
        self.assertFalse(any(p.startswith("Title:") for p in result))

    def test_description_included(self):
        result = extract_metadata_prompt(self._ctx(description="A nice description"))
        self.assertIn("Description: A nice description", result)

    def test_language_token_object(self):
        lang = SimpleNamespace(token="en")
        result = extract_metadata_prompt(self._ctx(language=lang))
        self.assertIn("Language: en", result)

    def test_language_string(self):
        result = extract_metadata_prompt(self._ctx(language="fr"))
        self.assertIn("Language: fr", result)

    def test_geo_coverage_dict_with_group_and_locations(self):
        ctx = self._ctx(
            geo_coverage={
                "selectedGroup": {"label": "Europe"},
                "geolocation": [{"label": "Germany"}, {"label": "France"}],
            }
        )
        result = extract_metadata_prompt(ctx)
        self.assertTrue(any("Geographic coverage" in p for p in result))
        self.assertTrue(any("Europe" in p for p in result))
        self.assertTrue(any("Germany" in p for p in result))

    def test_geo_coverage_dict_locations_only(self):
        ctx = self._ctx(
            geo_coverage={
                "selectedGroup": {},
                "geolocation": [{"label": "Spain"}],
            }
        )
        result = extract_metadata_prompt(ctx)
        self.assertIn("Geographic coverage: Spain", result)

    def test_geo_coverage_string(self):
        result = extract_metadata_prompt(self._ctx(geo_coverage="Global"))
        self.assertIn("Geographic coverage: Global", result)

    def test_geo_coverage_excluded_when_flag_false(self):
        result = extract_metadata_prompt(
            self._ctx(geo_coverage="Global"), include_geo_coverage=False
        )
        self.assertFalse(any("Geographic coverage" in p for p in result))

    def test_temporal_coverage_list(self):
        result = extract_metadata_prompt(
            self._ctx(temporal_coverage=[2020, 2021, 2022])
        )
        self.assertIn("Temporal coverage: 2020, 2021, 2022", result)

    def test_temporal_coverage_string(self):
        result = extract_metadata_prompt(self._ctx(temporal_coverage="2020-2023"))
        self.assertIn("Temporal coverage: 2020-2023", result)

    def test_temporal_coverage_excluded_when_flag_false(self):
        result = extract_metadata_prompt(
            self._ctx(temporal_coverage=[2020, 2021]),
            include_temporal_coverage=False,
        )
        self.assertFalse(any("Temporal coverage" in p for p in result))

    def test_llm_summary_excluded_by_default(self):
        result = extract_metadata_prompt(
            self._ctx(llm_summary="An existing summary")
        )
        self.assertFalse(any("LLM summary" in p for p in result))

    def test_llm_summary_included_when_flag_true(self):
        result = extract_metadata_prompt(
            self._ctx(llm_summary="An existing summary"),
            include_llm_summary=True,
        )
        self.assertIn("LLM summary: An existing summary", result)

    def test_all_fields_combined(self):
        ctx = self._ctx(
            title="Water Report",
            description="Annual water quality overview",
            language="en",
            geo_coverage="Europe",
            temporal_coverage=[2022, 2023],
        )
        result = extract_metadata_prompt(ctx)
        self.assertIn("Title: Water Report", result)
        self.assertIn("Description: Annual water quality overview", result)
        self.assertIn("Language: en", result)
        self.assertIn("Geographic coverage: Europe", result)
        self.assertIn("Temporal coverage: 2022, 2023", result)


class TestGenericMetadataProviderConfig(unittest.TestCase):
    def test_name(self):
        self.assertEqual(GenericMetadataProvider.name, "generic_metadata")

    def test_include_llm_summary_is_false_by_default(self):
        self.assertFalse(GenericMetadataProvider.include_llm_summary)

    def test_include_temporal_coverage_is_true(self):
        self.assertTrue(GenericMetadataProvider.include_temporal_coverage)

    def test_include_geo_coverage_is_true(self):
        self.assertTrue(GenericMetadataProvider.include_geo_coverage)


class TestGenericMetadataNoDatesProviderConfig(unittest.TestCase):
    def test_name(self):
        self.assertEqual(
            GenericMetadataNoDatesProvider.name, "generic_metadata_no_dates"
        )

    def test_temporal_coverage_is_false(self):
        self.assertFalse(GenericMetadataNoDatesProvider.include_temporal_coverage)

    def test_geo_coverage_still_true(self):
        self.assertTrue(GenericMetadataNoDatesProvider.include_geo_coverage)


class TestSummarizerAgentConfig(unittest.TestCase):
    def test_system_prompt_is_set(self):
        self.assertTrue(SummarizerAgent.system_prompt)

    def test_system_prompt_mentions_content(self):
        self.assertIn("content", SummarizerAgent.system_prompt.lower())

    def test_task_prompt_is_set(self):
        self.assertTrue(SummarizerAgent.task_prompt)

    def test_task_prompt_mentions_summary(self):
        self.assertIn("summary", SummarizerAgent.task_prompt.lower())

    def test_context_providers_include_generic_metadata(self):
        self.assertIn("generic_metadata", SummarizerAgent.context_providers)

    def test_context_providers_include_blocks(self):
        self.assertIn("blocks", SummarizerAgent.context_providers)
