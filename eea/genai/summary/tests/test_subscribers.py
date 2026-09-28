"""Unit tests for the summary subscribers (no Plone bootstrap)."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from eea.genai.summary.subscribers import on_content_created, on_content_modified


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


class TestOnContentCreatedGate(unittest.TestCase):
    """The created-event handler must only fire for objects that carry
    actual image data at creation time."""

    @patch("eea.genai.summary.subscribers.on_content_modified")
    def test_no_image_field_skips(self, mock_mod):
        on_content_created(SimpleNamespace(image=None), None)
        mock_mod.assert_not_called()

    @patch("eea.genai.summary.subscribers.on_content_modified")
    def test_empty_image_skips(self, mock_mod):
        obj = _obj(image=SimpleNamespace(getSize=lambda: 0))
        on_content_created(obj, None)
        mock_mod.assert_not_called()

    @patch("eea.genai.summary.subscribers.on_content_modified")
    def test_image_with_data_delegates(self, mock_mod):
        obj = _obj(image=SimpleNamespace(getSize=lambda: 1234))
        on_content_created(obj, None)
        mock_mod.assert_called_once_with(obj, None)

    @patch("eea.genai.summary.subscribers.on_content_modified")
    def test_size_accessor_error_skips(self, mock_mod):
        def _boom():
            raise RuntimeError("blob gone")

        obj = _obj(image=SimpleNamespace(getSize=_boom))
        on_content_created(obj, None)
        mock_mod.assert_not_called()
