"""LLM summary generation endpoints"""

import logging

from plone import api
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service

from eea.genai.summary.behaviors import ILLMSummary
from eea.genai.summary.generate import generate_summary_for

logger = logging.getLogger("eea.genai.summary")


class LLMSummaryPost(Service):
    """POST @llm-summary - generate LLM summary for a single content object"""

    def reply(self):
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
    """POST @llm-summary-batch - generate LLM summaries for multiple objects"""

    def reply(self):
        body = json_body(self.request)
        limit = body.get("limit", 10)
        offset = body.get("offset", 0)
        force = body.get("force", False)
        portal_type = body.get("portal_type", None)

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
        processed = 0

        for obj in batch:
            entry = {
                "@id": obj.absolute_url(),
                "title": obj.title,
            }

            if not force and getattr(obj, "llm_summary", None):
                entry["status"] = "skipped"
                entry["llm_summary"] = obj.llm_summary
                results.append(entry)
                continue

            try:
                result = generate_summary_for(obj, self.request)
                if result:
                    summary = result.get("llm_summary")
                    if summary and summary.strip():
                        obj.llm_summary = summary
                        obj.reindexObject(idxs=["modified"])
                entry["status"] = "success"
                entry.update(result)
                processed += 1
            except Exception as e:
                logger.warning(
                    "LLM summary batch failed for %s: %s",
                    obj.absolute_url(),
                    str(e),
                )
                entry["status"] = "error"
                entry["error"] = str(e)

            results.append(entry)

        return {
            "total": total,
            "processed": processed,
            "offset": offset,
            "limit": limit,
            "results": results,
        }
