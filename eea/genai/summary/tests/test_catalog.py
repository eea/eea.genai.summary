"""Unit tests for the llm_summary catalog metadata column helper."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from eea.genai.summary.catalog import (
    LLM_SUMMARY_CATALOG_COLUMN,
    ensure_llm_summary_catalog_column,
)


def _catalog(columns=()):
    added = []

    def add_column(name, default_value=None):
        added.append(name)

    catalog = SimpleNamespace(
        schema=lambda: list(columns),
        addColumn=add_column,
    )
    return catalog, added


def _context_with_catalog(catalog):
    return SimpleNamespace(portal_catalog=catalog)


def _no_permission_manager():
    return SimpleNamespace(checkPermission=lambda permission, obj: False)


def _manager():
    return SimpleNamespace(checkPermission=lambda permission, obj: True)


class TestEnsureLlmSummaryCatalogColumn(unittest.TestCase):
    def test_no_catalog_is_a_noop(self):
        # A context without the catalog tool (e.g. bare test doubles)
        # must not raise.
        ensure_llm_summary_catalog_column(SimpleNamespace())

    def test_existing_column_is_not_readded(self):
        catalog, added = _catalog(columns=[LLM_SUMMARY_CATALOG_COLUMN])
        ensure_llm_summary_catalog_column(_context_with_catalog(catalog))
        self.assertEqual(added, [])

    @patch("eea.genai.summary.catalog.getSecurityManager")
    def test_missing_column_added_for_manager(self, mock_sm):
        mock_sm.return_value = _manager()
        catalog, added = _catalog()
        ensure_llm_summary_catalog_column(_context_with_catalog(catalog))
        self.assertEqual(added, [LLM_SUMMARY_CATALOG_COLUMN])

    @patch("eea.genai.summary.catalog.getSecurityManager")
    def test_missing_column_not_added_without_permission(self, mock_sm):
        # The auto-generation subscriber runs in the requesting
        # editor's context; only a manager may alter the catalog schema.
        mock_sm.return_value = _no_permission_manager()
        catalog, added = _catalog()
        ensure_llm_summary_catalog_column(_context_with_catalog(catalog))
        self.assertEqual(added, [])


class TestSubscriberEnsuresColumn(unittest.TestCase):
    """The auto-generation write path ensures the column before the
    summary reindex, so the fresh summary lands in brain metadata."""

    @patch("eea.genai.summary.subscribers.ensure_llm_summary_catalog_column")
    @patch("eea.genai.summary.subscribers.generate_summary_for")
    def test_ensured_before_reindex(self, mock_gen, mock_ensure):
        from eea.genai.summary.subscribers import on_content_modified

        mock_gen.return_value = {"llm_summary": "New summary."}
        obj = SimpleNamespace(
            allow_llm_summary=True,
            llm_summary=None,
            absolute_url=lambda: "http://nohost/en/img",
            reindexObject=lambda **kw: None,
        )
        on_content_modified(obj, None)
        self.assertEqual(obj.llm_summary, "New summary.")
        mock_ensure.assert_called_once_with(obj)
