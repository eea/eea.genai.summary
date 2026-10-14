"""Interfaces for eea.genai.summary"""

from plone.supermodel import model
from zope import schema
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from eea.genai.summary import EEAMessageFactory as _


class IImageAISettings(model.Schema):
    """Image settings contributed to the shared GenAI controlpanel."""

    model.fieldset(
        "image_ai",
        label=_("Image AI"),
        fields=[
            "image_ai_enabled",
            "image_title_alt_max_length",
            "image_description_max_length",
        ],
    )

    image_ai_enabled = schema.Bool(
        title=_("Enable Image AI features"),
        description=_(
            "Allow AI metadata generation for Image uploads and alt generation "
            "for Image blocks. The global GenAI switch must also be enabled."
        ),
        default=False,
        required=False,
    )
    image_title_alt_max_length = schema.Int(
        title=_("Maximum Image title/alt length"),
        description=_("Maximum generated title or alt length in characters."),
        default=64,
        min=1,
        required=True,
    )
    image_description_max_length = schema.Int(
        title=_("Maximum Image description length"),
        description=_("Maximum generated description length in characters."),
        default=500,
        min=1,
        required=True,
    )


class IGenAISummaryLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""
