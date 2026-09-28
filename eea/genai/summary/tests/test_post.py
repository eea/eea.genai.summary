"""Unit tests for @llm-summary-batch parameter validation."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from eea.genai.summary.restapi.post import (
    MAX_BATCH_LIMIT,
    _as_int,
    LLMSummaryBatchPost,
    parse_batch_params,
)


class TestAsInt(unittest.TestCase):
    def test_int_passes_through(self):
        self.assertEqual(_as_int(10), 10)

    def test_numeric_string_converts(self):
        self.assertEqual(_as_int("25"), 25)

    def test_none_returns_none(self):
        self.assertIsNone(_as_int(None))

    def test_garbage_returns_none(self):
        self.assertIsNone(_as_int("abc"))
        self.assertIsNone(_as_int(3.7))


class TestParseBatchParams(unittest.TestCase):
    def test_defaults(self):
        limit, offset, force, error = parse_batch_params({})
        self.assertEqual((limit, offset, force, error), (10, 0, False, None))

    def test_explicit_values(self):
        limit, offset, force, error = parse_batch_params(
            {"limit": 3, "offset": 7, "force": True}
        )
        self.assertEqual((limit, offset, force, error), (3, 7, True, None))

    def test_string_limit_accepted(self):
        limit, _, _, error = parse_batch_params({"limit": "5"})
        self.assertEqual((limit, error), (5, None))

    def test_limit_zero_rejected(self):
        _, _, _, error = parse_batch_params({"limit": 0})
        self.assertIn("limit", error)

    def test_negative_limit_rejected(self):
        _, _, _, error = parse_batch_params({"limit": -5})
        self.assertIn("limit", error)

    def test_garbage_limit_rejected(self):
        _, _, _, error = parse_batch_params({"limit": "abc"})
        self.assertIn("limit", error)

    def test_negative_offset_rejected(self):
        _, _, _, error = parse_batch_params({"offset": -1})
        self.assertIn("offset", error)

    def test_garbage_offset_rejected(self):
        _, _, _, error = parse_batch_params({"offset": None})
        self.assertIn("offset", error)

    def test_limit_capped_at_max(self):
        limit, _, _, error = parse_batch_params({"limit": 1000})
        self.assertEqual((limit, error), (MAX_BATCH_LIMIT, None))

    def test_custom_max_limit(self):
        limit, _, _, error = parse_batch_params({"limit": 100}, max_limit=5)
        self.assertEqual((limit, error), (5, None))

    def test_float_limit_rejected(self):
        _, _, _, error = parse_batch_params({"limit": 3.7})
        self.assertIn("limit", error)

    def test_bool_limit_rejected(self):
        _, _, _, error = parse_batch_params({"limit": True})
        self.assertIn("limit", error)

    def test_force_defaults_to_false_and_truthy_passes(self):
        self.assertFalse(parse_batch_params({})[2])
        self.assertFalse(parse_batch_params({"force": False})[2])
        self.assertTrue(parse_batch_params({"force": 1})[2])
        self.assertTrue(parse_batch_params({"force": True})[2])


class TestBatchReplyStatus(unittest.TestCase):
    """reply() status/counts/commit semantics (mocked catalog + generator)."""

    def _obj(self, id="obj1", summary=None, allow=True):
        from zope.interface import alsoProvides

        from eea.genai.summary.behaviors import ILLMSummary

        obj = SimpleNamespace(
            portal_type="Image",
            title=id,
            llm_summary=summary,
            allow_llm_summary=allow,
            reindexObject=Mock(),
        )
        obj.absolute_url = lambda: f"http://host/eea/en/{id}"
        alsoProvides(obj, ILLMSummary)
        return obj

    def _run(self, body, objects):
        svc = LLMSummaryBatchPost()
        svc.context = SimpleNamespace()
        svc.request = SimpleNamespace(
            get=lambda key, default=None: (
                json.dumps(body) if key == "BODY" else default
            ),
            response=SimpleNamespace(setStatus=Mock()),
        )
        brains = [SimpleNamespace(getObject=lambda o=o: o) for o in objects]

        with patch("eea.genai.summary.restapi.post.api") as mock_api, patch(
            "eea.genai.summary.restapi.post.ensure_llm_summary_catalog_column"
        ), patch("eea.genai.summary.restapi.post.generate_summary_for") as mock_gen, patch(
            "eea.genai.summary.restapi.post.transaction"
        ) as mock_tx:
            mock_api.portal.get_tool.return_value = Mock(return_value=brains)
            response = svc.reply()
            return response, mock_gen, mock_tx

    def test_all_success(self):
        objs = [self._obj("a"), self._obj("b")]
        mock_gen = Mock()
        mock_gen.side_effect = [
            {"llm_summary": "A"},
            {"llm_summary": "B"},
        ]
        svc = LLMSummaryBatchPost()
        svc.context = SimpleNamespace()
        svc.request = SimpleNamespace(
            get=lambda key, default=None: (
                json.dumps({"force": True}) if key == "BODY" else default
            ),
            response=SimpleNamespace(setStatus=Mock()),
        )
        brains = [SimpleNamespace(getObject=lambda o=o: o) for o in objs]
        with patch("eea.genai.summary.restapi.post.api") as mock_api, patch(
            "eea.genai.summary.restapi.post.ensure_llm_summary_catalog_column"
        ), patch(
            "eea.genai.summary.restapi.post.generate_summary_for",
            mock_gen,
        ), patch("eea.genai.summary.restapi.post.transaction") as mock_tx:
            mock_api.portal.get_tool.return_value = Mock(return_value=brains)
            response = svc.reply()

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["succeeded"], 2)
        self.assertEqual(response["processed"], 2)
        self.assertEqual(mock_tx.commit.call_count, 2)
        mock_tx.abort.assert_not_called()

    def test_partial_on_one_error(self):
        objs = [self._obj("bad"), self._obj("good")]
        mock_gen = Mock()
        mock_gen.side_effect = [RuntimeError("boom"), {"llm_summary": "B"}]
        svc = LLMSummaryBatchPost()
        svc.context = SimpleNamespace()
        svc.request = SimpleNamespace(
            get=lambda key, default=None: (
                json.dumps({"force": True}) if key == "BODY" else default
            ),
            response=SimpleNamespace(setStatus=Mock()),
        )
        brains = [SimpleNamespace(getObject=lambda o=o: o) for o in objs]
        with patch("eea.genai.summary.restapi.post.api") as mock_api, patch(
            "eea.genai.summary.restapi.post.ensure_llm_summary_catalog_column"
        ), patch(
            "eea.genai.summary.restapi.post.generate_summary_for",
            mock_gen,
        ), patch("eea.genai.summary.restapi.post.transaction") as mock_tx:
            mock_api.portal.get_tool.return_value = Mock(return_value=brains)
            response = svc.reply()

        self.assertEqual(response["status"], "partial")
        self.assertEqual(
            [r["status"] for r in response["results"]], ["error", "success"]
        )
        self.assertIn("boom", response["results"][0]["error"])
        self.assertIsNone(objs[0].llm_summary)
        self.assertEqual(objs[1].llm_summary, "B")
        self.assertEqual(mock_tx.commit.call_count, 1)
        self.assertEqual(mock_tx.abort.call_count, 1)

    def test_no_matches_reports_error_with_hint(self):
        response, mock_gen, _ = self._run({"portal_type": "Image"}, [])
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["total"], 0)
        self.assertIn("portal_type", response["message"])
        mock_gen.assert_not_called()

    def test_skipped_without_force_is_success(self):
        objs = [self._obj("a", summary="existing")]
        response, mock_gen, mock_tx = self._run({}, objs)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["skipped"], 1)
        self.assertEqual(response["succeeded"], 0)
        self.assertEqual(response["results"][0]["status"], "skipped")
        mock_gen.assert_not_called()
        mock_tx.commit.assert_not_called()

    def test_empty_result_counts_as_empty_not_success(self):
        objs = [self._obj("a")]
        mock_gen = Mock()
        mock_gen.return_value = {"llm_summary": ""}
        svc = LLMSummaryBatchPost()
        svc.context = SimpleNamespace()
        svc.request = SimpleNamespace(
            get=lambda key, default=None: (
                json.dumps({"force": True}) if key == "BODY" else default
            ),
            response=SimpleNamespace(setStatus=Mock()),
        )
        brains = [SimpleNamespace(getObject=lambda o=o: o) for o in objs]
        with patch("eea.genai.summary.restapi.post.api") as mock_api, patch(
            "eea.genai.summary.restapi.post.ensure_llm_summary_catalog_column"
        ), patch(
            "eea.genai.summary.restapi.post.generate_summary_for",
            mock_gen,
        ), patch("eea.genai.summary.restapi.post.transaction") as mock_tx:
            mock_api.portal.get_tool.return_value = Mock(return_value=brains)
            response = svc.reply()

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["empty"], 1)
        self.assertEqual(response["succeeded"], 0)
        self.assertIsNone(objs[0].llm_summary)
        mock_tx.commit.assert_not_called()

    def test_invalid_limit_returns_400(self):
        svc = LLMSummaryBatchPost()
        svc.context = SimpleNamespace()
        svc.request = SimpleNamespace(
            get=lambda key, default=None: (
                json.dumps({"limit": 0}) if key == "BODY" else default
            ),
            response=SimpleNamespace(setStatus=Mock()),
        )
        with patch("eea.genai.summary.restapi.post.api") as mock_api:
            response = svc.reply()
        self.assertEqual(svc.request.response.setStatus.call_args[0][0], 400)
        self.assertIn("limit", response["error"])
        mock_api.portal.get_tool.assert_not_called()


if __name__ == "__main__":
    unittest.main()
