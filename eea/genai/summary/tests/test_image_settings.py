"""Image AI settings defaults and registry-backed feature gating."""

import unittest

from plone.registry import Registry
from plone.registry.fieldfactory import persistentFieldAdapter
from plone.registry.interfaces import IRegistry
from zope.component import getGlobalSiteManager, provideAdapter, provideUtility
from zope.publisher.browser import TestRequest
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import TooSmall
from zope.component.testing import setUp, tearDown
import zope.schema.vocabulary as zsv

from eea.genai.core.settings import GENAI_SETTINGS_PREFIX
from eea.genai.summary.interfaces import IImageAISettings
from eea.genai.summary.settings import (
    ImageAISettingsSection,
    get_image_ai_limits,
    is_image_ai_allowed,
    is_image_ai_enabled,
)


class TestImageAISettings(unittest.TestCase):
    def test_contributed_fields_form_an_image_controlpanel_group(self):
        from plone.restapi.types.utils import get_fieldset_infos, get_fieldsets
        from eea.genai.core.interfaces import IGenAISettingsSection
        from eea.genai.core.settings import get_controlpanel_schema

        provideUtility(ImageAISettingsSection(), IGenAISettingsSection, name="image")
        fieldsets = get_fieldset_infos(
            get_fieldsets(None, TestRequest(), get_controlpanel_schema())
        )
        image_group = next(group for group in fieldsets if group["id"] == "image_ai")
        self.assertEqual(
            image_group["fields"],
            [
                "image_ai_enabled",
                "image_ai_allowed_content_types",
                "image_title_alt_max_length",
                "image_description_max_length",
            ],
        )
        self.assertIn("enabled", fieldsets[0]["fields"])

    def setUp(self):
        setUp()
        self.addCleanup(tearDown)
        provideAdapter(persistentFieldAdapter)
        self.registry = Registry()
        getGlobalSiteManager().registerUtility(self.registry, IRegistry)
        # In production, plone.app.vocabularies provides the content type
        # vocabulary via zope.componentvocabulary; stub it for binding here.
        self._vocabulary_registry = zsv.getVocabularyRegistry()
        zsv.setVocabularyRegistry(zsv.VocabularyRegistry())
        zsv.getVocabularyRegistry().register(
            "plone.app.vocabularies.ReallyUserFriendlyTypes",
            lambda context: SimpleVocabulary.fromValues(["Document", "Image"]),
        )
        self.addCleanup(zsv.setVocabularyRegistry, self._vocabulary_registry)

    def test_defaults_without_installed_records(self):
        self.assertFalse(is_image_ai_enabled())
        self.assertEqual(get_image_ai_limits(), (40, 500))
        # The default allow list covers standalone Image items only.
        self.assertTrue(is_image_ai_allowed("Image"))
        self.assertFalse(is_image_ai_allowed("Document"))
        self.assertEqual(
            ImageAISettingsSection().get_public_settings(),
            {"enabled": False, "allowed_content_types": ["Image"]},
        )

    def test_image_switch_and_master_switch_must_both_be_enabled(self):
        from eea.genai.core.interfaces import IGenAISettings

        self.registry.registerInterface(IImageAISettings, prefix=GENAI_SETTINGS_PREFIX)
        # Register just the core master switch; provider settings are unrelated.
        omit = tuple(name for name in IGenAISettings.names() if name != "enabled")
        self.registry.registerInterface(IGenAISettings, omit=omit)
        image = self.registry.forInterface(
            IImageAISettings, prefix=GENAI_SETTINGS_PREFIX
        )
        image.image_ai_enabled = True
        self.assertTrue(is_image_ai_enabled())
        self.registry[f"{GENAI_SETTINGS_PREFIX}.enabled"] = False
        self.assertFalse(is_image_ai_enabled())
        self.assertEqual(
            ImageAISettingsSection().get_public_settings(),
            {"enabled": True, "allowed_content_types": ["Image"]},
        )

    def test_content_type_allowlist_restricts_image_ai(self):
        self.registry.registerInterface(IImageAISettings, prefix=GENAI_SETTINGS_PREFIX)
        settings = self.registry.forInterface(
            IImageAISettings, prefix=GENAI_SETTINGS_PREFIX
        )
        # The installed default only allows standalone Image items.
        self.assertTrue(is_image_ai_allowed("Image"))
        self.assertFalse(is_image_ai_allowed("Document"))
        # Replacing the list restricts to exactly the chosen types.
        settings.image_ai_allowed_content_types = ("Document",)
        self.assertTrue(is_image_ai_allowed("Document"))
        self.assertFalse(is_image_ai_allowed("Image"))
        self.assertEqual(
            ImageAISettingsSection().get_public_settings(),
            {"enabled": False, "allowed_content_types": ["Document"]},
        )
        # Clearing the allow list restores access for all content types.
        settings.image_ai_allowed_content_types = ()
        self.assertTrue(is_image_ai_allowed("Image"))
        self.assertTrue(is_image_ai_allowed("Document"))
        self.assertEqual(
            ImageAISettingsSection().get_public_settings(),
            {"enabled": False, "allowed_content_types": []},
        )

    def test_admin_can_set_shared_short_text_and_description_limits(self):
        self.registry.registerInterface(IImageAISettings, prefix=GENAI_SETTINGS_PREFIX)
        settings = self.registry.forInterface(
            IImageAISettings, prefix=GENAI_SETTINGS_PREFIX
        )
        settings.image_title_alt_max_length = 80
        settings.image_description_max_length = 300
        self.assertEqual(get_image_ai_limits(), (80, 300))
        with self.assertRaises(TooSmall):
            settings.image_title_alt_max_length = 0
