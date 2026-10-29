"""Unit tests for the summary subscribers (no Plone bootstrap)."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from eea.genai.summary.subscribers import on_content_modified


def _obj(llm_summary=None, allow=True, image=None):
    return SimpleNamespace(
        portal_type="Image",
        allow_llm_summary=allow,
        llm_summary=llm_summary,
        image=image,
        absolute_url=lambda: "http://nohost/en/img",
        reindexObject=lambda **kw: None,
    )


class TestOnContentModified(unittest.TestCase):
    @patch("eea.genai.summary.subscribers.generate_summary_for")
    def test_existing_summary_skips_generation(self, mock_gen):
        on_content_modified(_obj(llm_summary="already there"), None)
        mock_gen.assert_not_called()

    @patch("eea.genai.summary.subscribers.generate_summary_for")
    def test_whitespace_summary_triggers_regeneration(self, mock_gen):
        mock_gen.return_value = {"llm_summary": "New summary."}
        on_content_modified(_obj(llm_summary="   "), None)
        mock_gen.assert_called_once()

    @patch("eea.genai.summary.subscribers.generate_summary_for")
    def test_empty_summary_generates_and_persists(self, mock_gen):
        mock_gen.return_value = {"llm_summary": "New summary."}
        obj = _obj(llm_summary=None)
        on_content_modified(obj, None)
        mock_gen.assert_called_once()
        self.assertEqual(obj.llm_summary, "New summary.")

    @patch("eea.genai.summary.subscribers.generate_summary_for")
    def test_disabled_behavior_skips(self, mock_gen):
        on_content_modified(_obj(allow=False), None)
        mock_gen.assert_not_called()

    @patch("eea.genai.summary.subscribers.generate_summary_for")
    def test_empty_agent_result_preserves_existing(self, mock_gen):
        mock_gen.return_value = {"llm_summary": ""}
        obj = _obj(llm_summary=None)
        on_content_modified(obj, None)
        self.assertIsNone(obj.llm_summary)
