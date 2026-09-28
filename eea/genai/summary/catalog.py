"""Catalog metadata handling for LLM summaries.

The Volto object browser serializes catalog brains with
``metadata_fields=_all``, which exposes catalog *metadata columns* only.
Without an ``llm_summary`` metadata column the AI summary can never reach
the browser's brains, and the image block would have to fetch the Image
object just to read it. A metadata column stores the value in the brain
for read/serialization purposes and makes no field queryable (no index is
created), so site search behavior is unaffected.
"""

from AccessControl import getSecurityManager
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal

LLM_SUMMARY_CATALOG_COLUMN = "llm_summary"


def ensure_llm_summary_catalog_column(context):
    """Ensure ``portal_catalog`` carries the ``llm_summary`` metadata column.

    Idempotent and cheap: a single membership check against the catalog
    schema. Called from the summary write paths (auto-generation
    subscriber and batch endpoint) right before the object is reindexed,
    so the freshly written summary lands in the brain metadata.

    Adding a column requires the ``Manage portal`` permission. The
    auto-generation subscriber runs in the requesting editor's context, so
    when a non-manager triggers the first summary generation on a site the
    column is left for the next privileged write (batch endpoint, manager
    save) to create; brains simply lack the value until then, and the
    frontend falls back to the title.

    ``catalog.addColumn`` only registers the column; populating it for
    previously summarized objects requires a (one-time) reindex.
    """
    catalog = getToolByName(context, "portal_catalog", None)
    if catalog is None:
        return
    if LLM_SUMMARY_CATALOG_COLUMN in catalog.schema():
        return
    if not getSecurityManager().checkPermission(ManagePortal, catalog):
        return
    catalog.addColumn(LLM_SUMMARY_CATALOG_COLUMN)
