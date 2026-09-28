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
    """Uninstall script."""
    # Handler-only uninstall: nothing to clean up. The llm_summary
    # portal_catalog metadata column (added at runtime by the summary
    # write paths or by the default profile's catalog.xml) is left in
    # place — it is inert without this package.
