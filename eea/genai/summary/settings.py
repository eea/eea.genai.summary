"""Image AI settings; core only knows the generic settings-section contract."""

from zope.interface import implementer

from eea.genai.core.errors import AgentDisabled
from eea.genai.core.interfaces import IGenAISettingsSection
from eea.genai.core.settings import get_settings_value, is_enabled
from eea.genai.summary.interfaces import IImageAISettings


def is_image_ai_enabled():
    """Both master and Image-specific switches must allow generation."""
    return is_enabled() and bool(
        get_settings_value(IImageAISettings, "image_ai_enabled")
    )


def require_image_ai_enabled():
    """Reject direct generation calls as well as REST requests when disabled."""
    if not is_image_ai_enabled():
        raise AgentDisabled("Image AI features are disabled in the controlpanel")


def get_image_ai_limits():
    """Return the shared title/alt and description character limits."""
    return (
        get_settings_value(IImageAISettings, "image_title_alt_max_length"),
        get_settings_value(IImageAISettings, "image_description_max_length"),
    )


@implementer(IGenAISettingsSection)
class ImageAISettingsSection:
    """ZCML-registered controlpanel fields and public Image feature flag."""

    schema = IImageAISettings

    def get_public_settings(self):
        return {
            "enabled": bool(get_settings_value(self.schema, "image_ai_enabled")),
        }
