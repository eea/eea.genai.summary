"""Interfaces for eea.genai.summary"""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IGenAISummaryLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""
