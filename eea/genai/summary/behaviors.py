"""LLM Summary behavior"""

from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import provider


@provider(IFormFieldProvider)
class ILLMSummary(model.Schema):
    """Behavior schema providing LLM summary fields."""

    allow_llm_summary = schema.Bool(
        title="Allow LLM Summary",
        description="Enable LLM-powered summary generation for this content",
        required=False,
        default=True,
    )

    llm_summary = schema.Text(
        title="LLM Summary",
        description="LLM-generated accessibility and analytical summary",
        required=False,
    )
