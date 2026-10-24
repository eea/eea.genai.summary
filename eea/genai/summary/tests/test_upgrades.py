"""Registry-only upgrade for sites with the original summary profile."""

import logging
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from xml.etree import ElementTree

from plone.app.registry.exportimport.handler import importRegistry
from plone.registry import Registry
from plone.registry.fieldfactory import (
    choicePersistentFieldAdapter,
    persistentFieldAdapter,
)
from plone.registry.interfaces import IRegistry
from zope.component import getGlobalSiteManager, provideAdapter
from zope.component.testing import setUp, tearDown
from zope.schema.vocabulary import SimpleVocabulary
import zope.schema.vocabulary as zsv

from eea.genai.core.interfaces import IGenAISettings
from eea.genai.core.settings import GENAI_SETTINGS_PREFIX, get_controlpanel_schema
from eea.genai.summary.interfaces import IImageAISettings
from eea.genai.summary.upgrades import install_image_ai_settings


PACKAGE = Path(__file__).resolve().parents[1]
PROFILE = "profile-eea.genai.summary:default"


class RegistryImportContext:
    """Supply the actual profile XML to Plone's registry importer."""

    def getLogger(self, name):
        return logging.getLogger(name)

    def isDirectory(self, name):
        return False

    def readDataFile(self, name):
        return (PACKAGE / "profiles" / "default" / name).read_bytes()

    def shouldPurge(self):
        return False


class TestImageAIRegistryUpgrade(unittest.TestCase):
    def setUp(self):
        setUp()
        self.addCleanup(tearDown)
        provideAdapter(persistentFieldAdapter)
        provideAdapter(choicePersistentFieldAdapter)
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
        # Existing core settings must not be imported or reset by this upgrade.
        self.registry.registerInterface(IGenAISettings)
        self.registry[f"{GENAI_SETTINGS_PREFIX}.enabled"] = False
        self.registry[f"{GENAI_SETTINGS_PREFIX}.llm_model"] = "existing-model"
        self.setup_tool = Mock()
        self.setup_tool.runImportStepFromProfile.side_effect = self.import_step

    def import_step(self, profile, step, *, run_dependencies, purge_old):
        self.assertEqual(profile, PROFILE)
        self.assertEqual(step, "plone.app.registry")
        self.assertFalse(run_dependencies)
        self.assertFalse(purge_old)
        importRegistry(RegistryImportContext())

    def test_installs_missing_image_defaults_without_changing_core(self):
        install_image_ai_settings(self.setup_tool)
        image = self.registry.forInterface(
            IImageAISettings, prefix=GENAI_SETTINGS_PREFIX
        )
        self.assertFalse(image.image_ai_enabled)
        self.assertEqual(image.image_ai_allowed_content_types, ("Image",))
        self.assertEqual(image.image_title_alt_max_length, 40)
        self.assertEqual(image.image_description_max_length, 500)
        self.assertFalse(self.registry[f"{GENAI_SETTINGS_PREFIX}.enabled"])
        self.assertEqual(
            self.registry[f"{GENAI_SETTINGS_PREFIX}.llm_model"], "existing-model"
        )
        self.assertEqual(
            len(self.registry.records),
            len(IGenAISettings.names()) + len(IImageAISettings.names()),
        )
        self.setup_tool.runImportStepFromProfile.assert_called_once_with(
            PROFILE, "plone.app.registry", run_dependencies=False, purge_old=False
        )
        self.setup_tool.getSite.assert_not_called()

    def test_repeated_upgrade_preserves_configured_image_values(self):
        install_image_ai_settings(self.setup_tool)
        image = self.registry.forInterface(
            IImageAISettings, prefix=GENAI_SETTINGS_PREFIX
        )
        image.image_ai_enabled = True
        image.image_ai_allowed_content_types = ("Document", "Image")
        image.image_title_alt_max_length = 80
        image.image_description_max_length = 300
        before = {name: self.registry[name] for name in self.registry.records}
        install_image_ai_settings(self.setup_tool)
        install_image_ai_settings(self.setup_tool)
        self.assertEqual(
            {name: self.registry[name] for name in self.registry.records}, before
        )

    def test_repairs_partial_image_records_without_resetting_existing_value(self):
        self.registry.registerInterface(IImageAISettings, prefix=GENAI_SETTINGS_PREFIX)
        self.registry[f"{GENAI_SETTINGS_PREFIX}.image_title_alt_max_length"] = 80
        del self.registry.records[f"{GENAI_SETTINGS_PREFIX}.image_ai_enabled"]
        del self.registry.records[
            f"{GENAI_SETTINGS_PREFIX}.image_description_max_length"
        ]
        install_image_ai_settings(self.setup_tool)
        image = self.registry.forInterface(
            IImageAISettings, prefix=GENAI_SETTINGS_PREFIX
        )
        self.assertFalse(image.image_ai_enabled)
        self.assertEqual(image.image_title_alt_max_length, 80)
        self.assertEqual(image.image_description_max_length, 500)

    def test_composed_controlpanel_proxy_can_read_image_fields_after_upgrade(self):
        from eea.genai.core.interfaces import IGenAISettingsSection
        from eea.genai.summary.settings import ImageAISettingsSection
        from zope.component import provideUtility

        provideUtility(ImageAISettingsSection(), IGenAISettingsSection, name="image")
        schema = get_controlpanel_schema()
        with self.assertRaisesRegex(KeyError, "image_ai_enabled"):
            self.registry.forInterface(schema, prefix=GENAI_SETTINGS_PREFIX)
        install_image_ai_settings(self.setup_tool)
        settings = self.registry.forInterface(schema, prefix=GENAI_SETTINGS_PREFIX)
        self.assertFalse(settings.image_ai_enabled)
        self.assertEqual(settings.image_title_alt_max_length, 40)


class TestUpgradeRegistration(unittest.TestCase):
    def test_zcml_registers_an_executable_summary_only_upgrade(self):
        from Products import GenericSetup
        from Products.GenericSetup import upgrade
        from zope.configuration import xmlconfig
        from eea.genai.summary import upgrades

        registry = upgrade.UpgradeRegistry()
        # Isolate GenericSetup's global upgrade storage from other test modules.
        registry._registry = {}
        with patch.object(upgrade, "_upgrade_registry", registry):
            context = xmlconfig.file("meta.zcml", GenericSetup)
            xmlconfig.file("configure.zcml", upgrades, context=context)
            steps = registry.getUpgradeStepsForProfile(PROFILE)
            by_range = {(step.source, step.dest): step for step in steps.values()}
            self.assertEqual(
                sorted(by_range),
                [(("1", "0"), ("2", "0")), (("2", "0"), ("2", "1"))],
            )
            for step in by_range.values():
                self.assertIs(step.handler, install_image_ai_settings)
            self.assertEqual(list(registry.keys()), ["eea.genai.summary:default"])
            setup_tool = Mock()
            by_range[(("1", "0"), ("2", "0"))].doStep(setup_tool)
            by_range[(("2", "0"), ("2", "1"))].doStep(setup_tool)
            self.assertEqual(setup_tool.runImportStepFromProfile.call_count, 2)
            setup_tool.runImportStepFromProfile.assert_called_with(
                PROFILE, "plone.app.registry", run_dependencies=False, purge_old=False
            )

    def test_registry_upgrade_matches_profile_version_and_is_included(self):
        namespace = "{http://namespaces.zope.org/genericsetup}"
        root = ElementTree.parse(PACKAGE / "upgrades" / "configure.zcml").getroot()
        steps = root.findall(f"{namespace}upgradeStep")
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].get("profile"), "eea.genai.summary:default")
        self.assertEqual(steps[0].get("source"), "1.0")
        self.assertEqual(steps[0].get("destination"), "2.0")
        self.assertEqual(steps[0].get("handler"), ".install_image_ai_settings")
        self.assertEqual(steps[1].get("profile"), "eea.genai.summary:default")
        self.assertEqual(steps[1].get("source"), "2.0")
        self.assertEqual(steps[1].get("destination"), "2.1")
        self.assertEqual(steps[1].get("handler"), ".install_image_ai_settings")
        metadata = ElementTree.parse(PACKAGE / "profiles" / "default" / "metadata.xml")
        self.assertEqual(metadata.findtext("version"), "2.1")
        config = ElementTree.parse(PACKAGE / "configure.zcml").getroot()
        self.assertTrue(any(node.get("package") == ".upgrades" for node in config))
