"""LLM summary generation endpoints"""

import logging
import time
import uuid

import transaction
from plone import api
from plone.protect import interfaces as plone_protect_interfaces
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from zope.interface import alsoProvides

from eea.genai.summary.behaviors import ILLMSummary
from eea.genai.summary.catalog import ensure_llm_summary_catalog_column
from eea.genai.summary.generate import generate_summary_for

logger = logging.getLogger("eea.genai.summary")

#: Hard cap for the batch size on this admin endpoint.
MAX_BATCH_LIMIT = 50


def _disable_csrf(request):
    """Mark the request as exempt from CSRF checks.

    plone.protect aborts the transaction when a request writes to the
    ZODB without a form authenticator. REST API calls are authorized via
    permissions instead (same pattern as plone.restapi content services).
    """
    if "IDisableCSRFProtection" in dir(plone_protect_interfaces):
        alsoProvides(request, plone_protect_interfaces.IDisableCSRFProtection)


def _as_int(value):
    if isinstance(value, bool) or isinstance(value, float):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_batch_params(body, max_limit=MAX_BATCH_LIMIT):
    """Validate @llm-summary-batch request parameters.

    Returns ``(limit, offset, force, error)``. When ``error`` is not
    None the other values are meaningless.
    """
    limit = _as_int(body.get("limit", 10))
    offset = _as_int(body.get("offset", 0))
    force = bool(body.get("force", False))
    if limit is None or limit < 1:
        return None, None, force, "limit must be a positive integer"
    if offset is None or offset < 0:
        return None, None, force, "offset must be a non-negative integer"
    return min(limit, max_limit), offset, force, None


class LLMSummaryPost(Service):
    """POST @llm-summary - generate LLM summary for a single content object"""

    def reply(self):
        _disable_csrf(self.request)
        try:
            body = json_body(self.request)
            properties = body.get("properties", {})
            fields = generate_summary_for(
                self.context, self.request, properties=properties
            )
            return {
                "@id": self.context.absolute_url(),
                "title": self.context.title,
                **fields,
            }
        except Exception as e:
            logger.error(
                "LLM summary generation failed for %s: %s",
                self.context.absolute_url(),
                str(e),
            )
            self.request.response.setStatus(500)
            return {"error": str(e)}


class LLMSummaryBatchPost(Service):
    """POST @llm-summary-batch - generate LLM summaries for multiple objects

    Each object is committed individually (same pattern as
    eea.plotly's summarize endpoint) so completed objects survive later
    failures, and a per-object failure cannot roll back earlier work.
    """

    def reply(self):
        _disable_csrf(self.request)
        body = json_body(self.request)
        limit, offset, force, error = parse_batch_params(body)
        if error:
            self.request.response.setStatus(400)
            return {"error": error}
        portal_type = body.get("portal_type") or None

        run_id = uuid.uuid4().hex[:8]
        started = time.monotonic()
        logger.info(
            "[%s] Batch started: portal_type=%s limit=%d offset=%d force=%s",
            run_id,
            portal_type,
            limit,
            offset,
            force,
        )

        catalog = api.portal.get_tool("portal_catalog")
        query = {"sort_on": "path"}
        if portal_type:
            query["portal_type"] = portal_type

        brains = catalog(**query)

        # Filter to objects with ILLMSummary behavior and allow_llm_summary=True
        eligible = []
        for brain in brains:
            try:
                obj = brain.getObject()
            except Exception:
                continue
            if not ILLMSummary.providedBy(obj):
                continue
            if getattr(obj, "allow_llm_summary", False):
                eligible.append(obj)

        total = len(eligible)
        batch = eligible[offset : offset + limit]

        results = []
        counts = {"success": 0, "skipped": 0, "empty": 0, "error": 0}

        for obj in batch:
            entry = {
                "@id": obj.absolute_url(),
                "title": obj.title,
            }
            entry_started = time.monotonic()

            if not force and getattr(obj, "llm_summary", None):
                entry["status"] = "skipped"
                entry["llm_summary"] = obj.llm_summary
            else:
                try:
                    result = generate_summary_for(obj, self.request)
                    summary = (result or {}).get("llm_summary")
                    if summary and summary.strip():
                        obj.llm_summary = summary
                        ensure_llm_summary_catalog_column(obj)
                        obj.reindexObject(idxs=["modified"])
                        transaction.commit()
                        entry["status"] = "success"
                        entry.update(result)
                    else:
                        # The model could not produce a summary (e.g.
                        # unreadable image). Leave the object untouched
                        # and report it as "empty" so callers can
                        # distinguish it from success.
                        entry["status"] = "empty"
                except Exception as e:
                    # Discard this object's partial writes; earlier
                    # objects are already committed.
                    transaction.abort()
                    logger.exception(
                        "[%s] Batch failed for %s", run_id, obj.absolute_url()
                    )
                    entry["status"] = "error"
                    entry["error"] = str(e)

            counts[entry["status"]] += 1
            entry["duration_seconds"] = round(time.monotonic() - entry_started, 1)
            logger.info(
                "[%s] %s -> %s (%.1fs)",
                run_id,
                obj.absolute_url(),
                entry["status"],
                entry["duration_seconds"],
            )
            results.append(entry)

        duration = round(time.monotonic() - started, 1)
        failed = counts["error"] + counts["empty"]
        if total == 0:
            status = "error"
        elif failed == 0:
            status = "success"
        elif counts["success"] or counts["skipped"]:
            status = "partial"
        else:
            status = "error"

        logger.info(
            "[%s] Batch finished: status=%s total=%d success=%d skipped=%d "
            "empty=%d error=%d duration=%.1fs",
            run_id,
            status,
            total,
            counts["success"],
            counts["skipped"],
            counts["empty"],
            counts["error"],
            duration,
        )

        response = {
            "run_id": run_id,
            "status": status,
            "total": total,
            "selected": len(batch),
            "succeeded": counts["success"],
            "skipped": counts["skipped"],
            "empty": counts["empty"],
            "errors": counts["error"],
            "duration_seconds": duration,
            # Backward-compatible keys
            "processed": counts["success"],
            "offset": offset,
            "limit": limit,
            "results": results,
        }
        if total == 0:
            response["message"] = (
                "No matching objects found. Check portal_type "
                "(content types are case-sensitive)."
            )
        elif len(batch) == 0:
            response["message"] = (
                f"offset {offset} is beyond the number of matching "
                f"objects (total {total})."
            )
        return response
