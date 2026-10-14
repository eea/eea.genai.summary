"""Stateless REST services for Image metadata and alt generation."""

import logging
import re

from plone.restapi.deserializer import json_body
from plone.restapi.services import Service

from eea.genai.core.errors import AgentDisabled
from eea.genai.summary.settings import require_image_ai_enabled
from eea.genai.summary.generate import (
    generate_image_alt,
    generate_image_metadata,
)
from eea.genai.summary.image import (
    MAX_IMAGE_REQUEST_BYTES,
    ImageInputError,
    decode_transient_image,
)

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


def is_image_addable(context):
    """Check current-principal FTI availability and local type constraints."""
    allowed_content_types = getattr(context, "allowedContentTypes", None)
    if not callable(allowed_content_types):
        return False
    try:
        allowed = allowed_content_types()
    except Exception:
        return False
    for fti in allowed:
        get_id = getattr(fti, "getId", None)
        type_id = get_id() if callable(get_id) else getattr(fti, "id", None)
        if type_id == "Image":
            return True
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
            if not is_image_addable(self.context):
                return _error(
                    self,
                    403,
                    "image_not_addable",
                    "An Image cannot be added to this container.",
                )
            body = _body(self)
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


class ImageAltPost(Service):
    """Generate a block-local alt suggestion without persisting it."""

    def reply(self):
        try:
            require_image_ai_enabled()
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
