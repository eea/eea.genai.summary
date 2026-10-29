"""Stateless REST services for Image metadata and alt generation."""

import logging
import re

from plone.dexterity.utils import iterSchemata
from plone.namedfile.interfaces import INamedImageField
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from zope.schema import getFields

from eea.genai.core.errors import AgentDisabled
from eea.genai.summary.generate import (
    generate_image_alt,
    generate_image_metadata,
)
from eea.genai.summary.image import (
    MAX_IMAGE_REQUEST_BYTES,
    ImageInputError,
    decode_transient_image,
    transient_image_from_named_image,
)
from eea.genai.summary.settings import is_image_ai_allowed, require_image_ai_enabled

logger = logging.getLogger("eea.genai.summary")

_LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")


def safe_language(value):
    """Return a bounded language code or the documented English fallback."""
    if not isinstance(value, str):
        return "en"
    value = value.strip()
    if len(value) > 35 or not _LANGUAGE_RE.fullmatch(value):
        return "en"
    return value


def is_image_addable(context, portal_type="Image"):
    """Check the requested FTI's construction permission and local constraints."""
    allowed_content_types = getattr(context, "allowedContentTypes", None)
    if not callable(allowed_content_types):
        return False
    try:
        for fti in allowed_content_types():
            if fti.getId() == portal_type:
                return bool(fti.isConstructionAllowed(context))
    except Exception:
        return False
    return False


def _error(service, status, code, message):
    service.request.response.setStatus(status)
    return {"error": {"code": code, "message": message}}


def _body(service):
    raw_body = service.request.get("BODY", b"")
    if isinstance(raw_body, (bytes, str)) and len(raw_body) > MAX_IMAGE_REQUEST_BYTES:
        raise ImageInputError(
            "image_too_large",
            "The submitted image request is too large.",
            status=413,
        )
    try:
        body = json_body(service.request)
    except Exception as exc:
        raise ImageInputError(
            "invalid_request", "The request body must be valid JSON."
        ) from exc
    if not isinstance(body, dict):
        raise ImageInputError(
            "invalid_request", "The request body must be a JSON object."
        )
    return body


class ImageMetadataPost(Service):
    """Generate title and description before ordinary Image creation."""

    def reply(self):
        try:
            require_image_ai_enabled()
            body = _body(self)
            portal_type = body.get("portal_type", "Image")
            if (
                not isinstance(portal_type, str)
                or not portal_type
                or len(portal_type) > 200
            ):
                raise ImageInputError(
                    "invalid_request", "A valid target content type is required."
                )
            if not is_image_ai_allowed(portal_type):
                return _error(
                    self,
                    403,
                    "image_ai_not_allowed",
                    "Image AI is not allowed for this content type.",
                )
            if not is_image_addable(self.context, portal_type):
                return _error(
                    self,
                    403,
                    "image_not_addable",
                    "The requested content type cannot be added to this container.",
                )
            image = decode_transient_image(body.get("image"))
            language = safe_language(body.get("language"))
            return generate_image_metadata(
                image,
                self.request,
                language=language,
            )
        except AgentDisabled:
            return _error(
                self, 403, "image_ai_disabled", "Image AI features are disabled."
            )
        except ImageInputError as exc:
            return _error(self, exc.status, exc.code, exc.message)
        except Exception:
            logger.warning("Image metadata generation failed")
            return _error(
                self,
                502,
                "generation_failed",
                "Image metadata could not be generated.",
            )


def _get_named_image(context, name):
    """Retrieve a named image from context or its behavior adapters."""
    val = getattr(context, name, None)
    if val is not None and (hasattr(val, "data") or hasattr(val, "contentType")):
        return val
    for schema in iterSchemata(context):
        try:
            adapted = schema(context)
            val = getattr(adapted, name, None)
            if val is not None and (
                hasattr(val, "data") or hasattr(val, "contentType")
            ):
                return val
        except TypeError:
            continue
    return None


def _is_image_field(context, name):
    """Check if name is an image field or contains a named image on context."""
    if _get_named_image(context, name) is not None:
        return True
    for schema in iterSchemata(context):
        field = getFields(schema).get(name)
        if field is not None and INamedImageField.providedBy(field):
            return True
    return False


class ImageMetadataRegeneratePost(Service):
    """Suggest metadata from an existing object's stored or replacement image."""

    def reply(self):
        try:
            require_image_ai_enabled()
            if not is_image_ai_allowed(self.context.portal_type):
                return _error(
                    self,
                    403,
                    "image_ai_not_allowed",
                    "Image AI is not allowed for this content type.",
                )
            body = _body(self)
            name = body.get("field")
            if not isinstance(name, str) or not name or len(name) > 200:
                raise ImageInputError(
                    "invalid_request", "A schema image field is required."
                )
            if not _is_image_field(self.context, name):
                raise ImageInputError(
                    "invalid_request", "The requested field is not an image field."
                )
            if "image" in body:
                image = decode_transient_image(body["image"])
            else:
                named_image = _get_named_image(self.context, name)
                if named_image is None:
                    raise ImageInputError(
                        "invalid_request", "The requested image field has no image."
                    )
                image = transient_image_from_named_image(named_image)

            return generate_image_metadata(
                image, self.request, language=safe_language(body.get("language"))
            )
        except AgentDisabled:
            return _error(
                self, 403, "image_ai_disabled", "Image AI features are disabled."
            )
        except ImageInputError as exc:
            return _error(self, exc.status, exc.code, exc.message)
        except Exception:
            logger.warning("Image metadata regeneration failed")
            return _error(
                self, 502, "generation_failed", "Image metadata could not be generated."
            )


class ImageAltPost(Service):
    """Generate a block-local alt suggestion without persisting it."""

    def reply(self):
        try:
            require_image_ai_enabled()
            if not is_image_ai_allowed(self.context.portal_type):
                return _error(
                    self,
                    403,
                    "image_ai_not_allowed",
                    "Image AI is not allowed for this content type.",
                )
            body = _body(self)
            language = safe_language(body.get("language"))
            return generate_image_alt(
                self.context,
                self.request,
                language=language,
            )
        except AgentDisabled:
            return _error(
                self, 403, "image_ai_disabled", "Image AI features are disabled."
            )
        except ImageInputError as exc:
            return _error(self, exc.status, exc.code, exc.message)
        except Exception:
            logger.warning("Image alt generation failed")
            return _error(
                self,
                502,
                "generation_failed",
                "Image alt text could not be generated.",
            )
