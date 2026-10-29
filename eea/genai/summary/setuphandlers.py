"""Custom setup handlers."""

from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):
    """Hide the uninstall profile from site-creation and quickinstaller."""

    def getNonInstallableProfiles(self):
        return [
            "eea.genai.summary:uninstall",
        ]


def uninstall(context):
    """Uninstall script; this package creates no persistent catalog schema."""
