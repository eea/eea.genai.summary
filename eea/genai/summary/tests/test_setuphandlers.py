"""Unit tests for the GS setup handlers."""

import unittest
from types import SimpleNamespace

from eea.genai.summary.setuphandlers import (
    HiddenProfiles,
    uninstall,
)


class TestHiddenProfiles(unittest.TestCase):
    def test_uninstall_profile_hidden_from_quickinstaller(self):
        hidden = HiddenProfiles().getNonInstallableProfiles()
        self.assertEqual(hidden, ["eea.genai.summary:uninstall"])


class TestUninstallHandler(unittest.TestCase):
    def test_uninstall_is_a_noop(self):
        # Handler-only uninstall: must not raise and must not require
        # any catalog or site access.
        uninstall(SimpleNamespace())
