"""Public REST contracts for metadata suggestions on existing objects."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from plone.autoform.interfaces import READ_PERMISSIONS_KEY, WRITE_PERMISSIONS_KEY
from plone.namedfile.field import NamedBlobImage
from z3c.form.datamanager import AttributeField
from z3c.form.interfaces import IDataManager
from zope.component import provideAdapter, provideUtility
from zope.component.testing import setUp, tearDown
from zope.interface import Interface, alsoProvides
from zope.schema import Text, TextLine
from zope.schema.interfaces import IField
from zope.security.interfaces import IPermission
from zope.security.permission import Permission

from eea.genai.summary.tests.test_image_restapi import (
    _metadata_payload,
    _png_bytes,
    _request,
    _services_by_name,
)


class ICoreMetadata(Interface):
    title = TextLine()
    description = Text()


class IMetadata(ICoreMetadata):
    image = NamedBlobImage()
    preview_image = NamedBlobImage()


class IPreview(Interface):
    preview_image = NamedBlobImage()


class TestImageMetadataRegeneration(unittest.TestCase):
    def setUp(self):
        setUp()
        self.addCleanup(tearDown)
        provideAdapter(AttributeField, (Interface, IField), IDataManager)
        self.context = SimpleNamespace(
            portal_type="Image",
            title="Editor title",
            description="Editor description.",
            image=SimpleNamespace(
                data=_png_bytes(), contentType="image/png", filename="stored.png"
            ),
        )
        alsoProvides(self.context, IMetadata)
        self.schema_patch = patch(
            "eea.genai.summary.restapi.image.iterSchemata", return_value=[IMetadata]
        )
        self.schema_patch.start()
        self.addCleanup(self.schema_patch.stop)
        for name in ("require_image_ai_enabled", "is_image_ai_allowed"):
            mocked = patch(f"eea.genai.summary.restapi.image.{name}", return_value=True)
            mocked.start()
            self.addCleanup(mocked.stop)
        security = patch("eea.genai.summary.restapi.image.getSecurityManager")
        self.security = security.start().return_value
        self.security.checkPermission.return_value = True
        self.addCleanup(security.stop)

    def service(self, payload=None):
        from eea.genai.summary.restapi.image import ImageMetadataRegeneratePost

        service = ImageMetadataRegeneratePost()
        service.context = self.context
        service.request = _request(
            payload if payload is not None else {"field": "image", "language": "fr"}
        )
        return service

    def test_registration_supports_non_folderish_dexterity_with_modify_permission(self):
        service = _services_by_name()["@image-metadata-regenerate"]
        self.assertEqual(service["method"], "POST")
        self.assertEqual(service["permission"], "cmf.ModifyPortalContent")
        self.assertEqual(service["for"], "plone.dexterity.interfaces.IDexterityContent")

    def test_returns_suggestions_from_stored_field_without_mutating_object(self):
        service = self.service()
        before = dict(vars(self.context))
        with patch(
            "eea.genai.summary.restapi.image.generate_image_metadata"
        ) as generate:
            generate.return_value = {
                "title": "Heron in reeds",
                "description": "A heron stands in reeds.",
            }
            result = service.reply()
        self.assertEqual(result, generate.return_value)
        self.assertEqual(generate.call_args.args[0].filename, "stored.png")
        self.assertEqual(generate.call_args.kwargs["language"], "fr")
        self.assertEqual(vars(self.context), before)
        service.request.response.setStatus.assert_not_called()

    def test_replacement_bytes_take_precedence_over_stored_image(self):
        payload = _metadata_payload()
        payload["field"] = "image"
        service = self.service(payload)
        with patch(
            "eea.genai.summary.restapi.image.generate_image_metadata"
        ) as generate:
            generate.return_value = {
                "title": "Replacement",
                "description": "A replacement.",
            }
            result = service.reply()
        self.assertEqual(result, generate.return_value)
        self.assertEqual(generate.call_args.args[0].filename, "wetland.png")
        self.assertEqual(self.context.image.filename, "stored.png")
        self.assertEqual(self.context.title, "Editor title")

    def test_uses_explicit_preview_image_field_on_an_allowed_chart(self):
        self.context.portal_type = "Chart"
        self.context.preview_image = SimpleNamespace(
            data=_png_bytes(), contentType="image/png", filename="chart.png"
        )
        with patch(
            "eea.genai.summary.restapi.image.generate_image_metadata"
        ) as generate:
            self.service({"field": "preview_image"}).reply()
        self.assertEqual(generate.call_args.args[0].filename, "chart.png")

    def test_adapts_behavior_backed_image_field(self):
        behavior = SimpleNamespace(preview_image=self.context.image)
        provideAdapter(lambda context: behavior, (IMetadata,), IPreview)
        with patch(
            "eea.genai.summary.restapi.image.iterSchemata",
            return_value=[ICoreMetadata, IPreview],
        ), patch("eea.genai.summary.restapi.image.generate_image_metadata") as generate:
            self.service({"field": "preview_image"}).reply()
        self.assertEqual(generate.call_args.args[0].filename, "stored.png")

    def test_excluded_actual_type_cannot_be_spoofed_by_request(self):
        self.context.portal_type = "Chart"
        service = self.service({"field": "image", "portal_type": "Image"})
        with patch(
            "eea.genai.summary.restapi.image.is_image_ai_allowed", return_value=False
        ) as allowed, patch(
            "eea.genai.summary.restapi.image.generate_image_metadata"
        ) as generate:
            result = service.reply()
        allowed.assert_called_once_with("Chart")
        self.assertEqual(result["error"]["code"], "image_ai_not_allowed")
        service.request.response.setStatus.assert_called_once_with(403)
        generate.assert_not_called()

    def test_disabled_feature_rejects_before_reading_source(self):
        from eea.genai.core.errors import AgentDisabled

        service = self.service()
        with patch(
            "eea.genai.summary.restapi.image.require_image_ai_enabled",
            side_effect=AgentDisabled,
        ), patch(
            "eea.genai.summary.restapi.image.transient_image_from_named_image"
        ) as read:
            result = service.reply()
        self.assertEqual(result["error"]["code"], "image_ai_disabled")
        read.assert_not_called()

    def test_rejects_missing_unknown_or_non_image_fields(self):
        for name in (None, "does_not_exist", "title", "__dict__", 42):
            with self.subTest(field=name):
                service = self.service({"field": name})
                with patch(
                    "eea.genai.summary.restapi.image.generate_image_metadata"
                ) as generate:
                    result = service.reply()
                self.assertEqual(result["error"]["code"], "invalid_request")
                service.request.response.setStatus.assert_called_once_with(400)
                generate.assert_not_called()

    def test_denies_readonly_metadata_destination(self):
        field = IMetadata["title"]
        original = field.readonly
        field.readonly = True
        self.addCleanup(setattr, field, "readonly", original)
        service = self.service()
        with patch(
            "eea.genai.summary.restapi.image.generate_image_metadata"
        ) as generate:
            result = service.reply()
        self.assertEqual(result["error"]["code"], "image_not_editable")
        generate.assert_not_called()

    def test_enforces_source_read_and_metadata_write_permissions(self):
        permission = Permission("test.image.protected", "Protected image field")
        provideUtility(permission, IPermission, name=permission.id)
        self.security.checkPermission.side_effect = (
            lambda name, context: name != permission.title
        )
        for key, field in (
            (READ_PERMISSIONS_KEY, "image"),
            (WRITE_PERMISSIONS_KEY, "description"),
        ):
            with self.subTest(field=field):
                original = IMetadata.queryTaggedValue(key, {})
                IMetadata.setTaggedValue(key, {field: permission.id})
                try:
                    service = self.service()
                    with patch(
                        "eea.genai.summary.restapi.image.generate_image_metadata"
                    ) as generate:
                        result = service.reply()
                    self.assertEqual(result["error"]["code"], "image_not_editable")
                    generate.assert_not_called()
                finally:
                    IMetadata.setTaggedValue(key, original)

    def test_invalid_replacement_never_falls_back_to_stored_image(self):
        service = self.service(
            {"field": "image", "image": {"download": "https://example.com/private.png"}}
        )
        with patch(
            "eea.genai.summary.restapi.image.generate_image_metadata"
        ) as generate:
            result = service.reply()
        self.assertEqual(result["error"]["code"], "invalid_request")
        generate.assert_not_called()

    def test_rejects_ambiguous_image_fields(self):
        class IOtherImage(Interface):
            image = NamedBlobImage()

        service = self.service()
        with patch(
            "eea.genai.summary.restapi.image.iterSchemata",
            return_value=[IMetadata, IOtherImage],
        ):
            result = service.reply()
        self.assertEqual(result["error"]["code"], "invalid_request")
        service.request.response.setStatus.assert_called_once_with(400)

    def test_readonly_source_allows_stored_generation_but_not_replacement(self):
        field = IMetadata["image"]
        original = field.readonly
        field.readonly = True
        self.addCleanup(setattr, field, "readonly", original)
        with patch(
            "eea.genai.summary.restapi.image.generate_image_metadata"
        ) as generate:
            generate.return_value = {
                "title": "Read only source",
                "description": "An image.",
            }
            self.assertEqual(self.service().reply(), generate.return_value)
            payload = _metadata_payload()
            payload["field"] = "image"
            service = self.service(payload)
            self.assertEqual(service.reply()["error"]["code"], "image_not_editable")
            self.assertEqual(generate.call_count, 1)

    def test_enforces_data_manager_field_access_and_write_checks(self):
        for attribute in ("canAccess", "canWrite"):
            with self.subTest(attribute=attribute):
                manager = Mock()
                manager.canAccess.return_value = True
                manager.canWrite.return_value = True
                getattr(manager, attribute).return_value = False
                service = self.service()
                with patch(
                    "eea.genai.summary.restapi.image.queryMultiAdapter",
                    return_value=manager,
                ):
                    result = service.reply()
                self.assertEqual(result["error"]["code"], "image_not_editable")
                manager.query.assert_not_called()

    def test_checks_stored_size_before_reading_bytes(self):
        from eea.genai.summary.image import MAX_IMAGE_BYTES

        self.context.image = Mock(data=b"not read", contentType="image/png")
        self.context.image.getSize.return_value = MAX_IMAGE_BYTES + 1
        service = self.service()
        result = service.reply()
        self.assertEqual(result["error"]["code"], "image_too_large")
        service.request.response.setStatus.assert_called_once_with(413)

    def test_rejects_invalid_and_unsupported_stored_images(self):
        for media, data, code, status in (
            ("image/png", b"broken", "invalid_image", 400),
            ("image/jpeg", _png_bytes(), "invalid_image", 400),
            ("image/svg+xml", b"<svg/>", "unsupported_media_type", 415),
        ):
            with self.subTest(media=media):
                self.context.image = SimpleNamespace(data=data, contentType=media)
                service = self.service()
                result = service.reply()
                self.assertEqual(result["error"]["code"], code)
                service.request.response.setStatus.assert_called_once_with(status)

    def test_unknown_field_permission_is_not_treated_as_public(self):
        original = IMetadata.queryTaggedValue(READ_PERMISSIONS_KEY, {})
        IMetadata.setTaggedValue(
            READ_PERMISSIONS_KEY, {"image": "nonexistent.permission"}
        )
        self.addCleanup(IMetadata.setTaggedValue, READ_PERMISSIONS_KEY, original)
        service = self.service()
        self.assertEqual(service.reply()["error"]["code"], "image_not_editable")

    def test_provider_failure_does_not_expose_details_or_persist(self):
        service = self.service()
        with patch(
            "eea.genai.summary.restapi.image.generate_image_metadata",
            side_effect=RuntimeError("secret details"),
        ):
            result = service.reply()
        self.assertEqual(result["error"]["code"], "generation_failed")
        self.assertNotIn("secret details", result["error"]["message"])
        self.assertEqual(self.context.title, "Editor title")
