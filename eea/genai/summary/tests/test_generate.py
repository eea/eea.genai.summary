"""Unit tests for AI summary marker wrapping (issue #305021)."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from eea.genai.summary.generate import (
    SUMMARY_MARKER_END,
    SUMMARY_MARKER_START,
    generate_summary_for,
    wrap_with_ai_markers,
)


class TestWrapWithAiMarkers(unittest.TestCase):
    def test_wraps_plain_text(self):
        self.assertEqual(
            wrap_with_ai_markers("A red house."),
            f"{SUMMARY_MARKER_START} A red house. {SUMMARY_MARKER_END}",
        )

    def test_strips_outer_whitespace(self):
        self.assertEqual(
            wrap_with_ai_markers("  A red house.  \n"),
            f"{SUMMARY_MARKER_START} A red house. {SUMMARY_MARKER_END}",
        )

    def test_idempotent_on_wrapped_text(self):
        once = wrap_with_ai_markers("A red house.")
        self.assertEqual(wrap_with_ai_markers(once), once)

    def test_empty_string_stays_empty(self):
        self.assertEqual(wrap_with_ai_markers(""), "")
        self.assertEqual(wrap_with_ai_markers("   "), "")
        self.assertEqual(wrap_with_ai_markers(None), "")


class TestGenerateSummaryForMarkers(unittest.TestCase):
    """Marker gating in generate_summary_for (mocked executor/config)."""

    def _obj(self, portal_type="Image"):
        return SimpleNamespace(portal_type=portal_type)

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_wraps_when_agent_requests_markers(self, mock_exec, mock_cfg, mock_resolve):
        mock_resolve.return_value = "summarizer:Image"
        mock_cfg.return_value = {"summary_markers": True}
        mock_exec.return_value.run_with_agent.return_value = "A red house."

        result = generate_summary_for(self._obj(), request=None)

        self.assertEqual(
            result["llm_summary"],
            f"{SUMMARY_MARKER_START} A red house. {SUMMARY_MARKER_END}",
        )
        mock_exec.return_value.run_with_agent.assert_called_once()

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_no_wrap_without_markers(self, mock_exec, mock_cfg, mock_resolve):
        mock_resolve.return_value = "summarizer:visualization"
        mock_cfg.return_value = {}
        mock_exec.return_value.run_with_agent.return_value = "A red house."

        result = generate_summary_for(
            self._obj(portal_type="visualization"), request=None
        )

        self.assertEqual(result["llm_summary"], "A red house.")

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_non_string_result_not_wrapped(self, mock_exec, mock_cfg, mock_resolve):
        mock_resolve.return_value = "summarizer:Image"
        mock_cfg.return_value = {"summary_markers": True}
        structured = object()
        mock_exec.return_value.run_with_agent.return_value = structured

        result = generate_summary_for(self._obj(), request=None)

        self.assertIs(result["llm_summary"], structured)


class TestGenerateSummaryForLengthGuard(unittest.TestCase):
    """max_summary_length retry behavior in generate_summary_for."""

    def _obj(self):
        return SimpleNamespace(portal_type="Image")

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_within_limit_no_retry(self, mock_exec, mock_cfg, mock_resolve):
        mock_resolve.return_value = "summarizer:Image"
        mock_cfg.return_value = {"max_summary_length": 125}
        mock_exec.return_value.run_with_agent.return_value = "A red house."

        result = generate_summary_for(self._obj(), request=None)

        self.assertEqual(result["llm_summary"], "A red house.")
        mock_exec.return_value.run_with_agent.assert_called_once()

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_overshoot_adopts_shorter_retry(self, mock_exec, mock_cfg, mock_resolve):
        mock_resolve.return_value = "summarizer:Image"
        mock_cfg.return_value = {"max_summary_length": 20}
        long_first = "A" * 50
        short_retry = "A red house."
        mock_exec.return_value.run_with_agent.side_effect = [
            long_first,
            short_retry,
        ]

        result = generate_summary_for(self._obj(), request=None)

        self.assertEqual(result["llm_summary"], short_retry)
        self.assertEqual(mock_exec.return_value.run_with_agent.call_count, 2)

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_overshoot_keeps_first_when_retry_longer(
        self, mock_exec, mock_cfg, mock_resolve
    ):
        mock_resolve.return_value = "summarizer:Image"
        mock_cfg.return_value = {"max_summary_length": 20}
        first = "A" * 50
        longer_retry = "B" * 60
        mock_exec.return_value.run_with_agent.side_effect = [
            first,
            longer_retry,
        ]

        result = generate_summary_for(self._obj(), request=None)

        self.assertEqual(result["llm_summary"], first)
        self.assertEqual(mock_exec.return_value.run_with_agent.call_count, 2)

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_retry_empty_keeps_first_result(self, mock_exec, mock_cfg, mock_resolve):
        """An empty retry must not discard a valid (if long) first result."""
        mock_resolve.return_value = "summarizer:Image"
        mock_cfg.return_value = {"max_summary_length": 20}
        first = "A" * 50
        mock_exec.return_value.run_with_agent.side_effect = [
            first,
            "",
        ]

        result = generate_summary_for(self._obj(), request=None)

        self.assertEqual(result["llm_summary"], first)
        self.assertEqual(mock_exec.return_value.run_with_agent.call_count, 2)

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_retry_failure_keeps_first_result(self, mock_exec, mock_cfg, mock_resolve):
        """A raising retry must not lose the first result or propagate."""
        mock_resolve.return_value = "summarizer:Image"
        mock_cfg.return_value = {"max_summary_length": 20}
        first = "A" * 50
        mock_exec.return_value.run_with_agent.side_effect = [
            first,
            RuntimeError("gateway timeout"),
        ]

        result = generate_summary_for(self._obj(), request=None)

        self.assertEqual(result["llm_summary"], first)
        self.assertEqual(mock_exec.return_value.run_with_agent.call_count, 2)

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_no_limit_never_retries(self, mock_exec, mock_cfg, mock_resolve):
        mock_resolve.return_value = "summarizer"
        mock_cfg.return_value = {}
        mock_exec.return_value.run_with_agent.return_value = "A" * 500

        result = generate_summary_for(self._obj(), request=None)

        self.assertEqual(result["llm_summary"], "A" * 500)
        mock_exec.return_value.run_with_agent.assert_called_once()

    @patch("eea.genai.summary.generate.get_agent_for_content_type")
    @patch("eea.genai.summary.generate.get_agent_config")
    @patch("eea.genai.summary.generate.get_executor")
    def test_non_string_result_never_retries(self, mock_exec, mock_cfg, mock_resolve):
        mock_resolve.return_value = "summarizer:Image"
        mock_cfg.return_value = {"max_summary_length": 20}
        structured = object()
        mock_exec.return_value.run_with_agent.return_value = structured

        result = generate_summary_for(self._obj(), request=None)

        self.assertIs(result["llm_summary"], structured)
        mock_exec.return_value.run_with_agent.assert_called_once()
