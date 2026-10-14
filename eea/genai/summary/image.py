"""Bounded multimodal image preparation and agent context helpers."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import io
import logging
import warnings

from eea.genai.core.interfaces import Enricher

logger = logging.getLogger("eea.genai.summary")

SUPPORTED_MEDIA_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}
)
MEDIA_TYPE_FORMATS = {
    "image/jpeg": frozenset({"JPEG"}),
    "image/png": frozenset({"PNG"}),
    "image/webp": frozenset({"WEBP"}),
    "image/gif": frozenset({"GIF"}),
    "image/bmp": frozenset({"BMP"}),
}

MAX_SIDE = 2048
JPEG_QUALITY = 85
NO_REENCODE_MAX_BYTES = 1_000_000

# Request/decode limits for untrusted transient uploads. The source limits are
# deliberately independent from Pillow defaults and are checked before load().
MAX_IMAGE_BYTES = 20_000_000
MAX_ENCODED_IMAGE_BYTES = 4 * ((MAX_IMAGE_BYTES + 2) // 3)
MAX_IMAGE_REQUEST_BYTES = MAX_ENCODED_IMAGE_BYTES + 4096
MAX_SOURCE_SIDE = 16_384
MAX_SOURCE_PIXELS = 40_000_000


class ImageInputError(ValueError):
    """Safe validation failure that can be returned by Image REST services."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class TransientImage:
    """In-memory named-image value consumed by ``ImageContentProvider``."""

    data: bytes
    contentType: str
    filename: str = "upload"

    def getSize(self):
        return len(self.data)


@dataclass
class TransientImageContext:
    """Non-persistent context exposing the fields used by Image enrichers."""

    image: TransientImage
    title: str = ""
    description: str = ""
    language: str = "en"
    portal_type: str = "Image"


def _read_image_data(image):
    if image is None:
        return None
    try:
        data = getattr(image, "data", None)
        if data is None:
            open_fn = getattr(image, "open", None)
            if callable(open_fn):
                with open_fn("r") as fp:
                    data = fp.read()
    except Exception:
        logger.warning("image_content: failed to read image data")
        return None
    if isinstance(data, (bytes, bytearray)):
        return bytes(data) or None
    return None


class ImageContentProvider(Enricher):
    """Attach the context's primary image to a multimodal agent prompt."""

    name = "image_content"
    description = "Attaches the image bytes of Image content to the prompt"
    image_field = "image"

    def _image(self, deps):
        context = getattr(deps, "context", None)
        if context is None:
            return None
        return getattr(context, self.image_field, None)

    def _image_data(self, image):
        return _read_image_data(image)

    def _image_present(self, image) -> bool:
        if image is None:
            return False
        size_fn = getattr(image, "getSize", None)
        if callable(size_fn):
            try:
                return bool(size_fn())
            except Exception:
                return False
        return self._image_data(image) is not None

    def user_prompt(self, deps) -> str:
        image = self._image(deps)
        if not self._image_present(image):
            return ""
        media_type = (getattr(image, "contentType", "") or "").lower()
        if media_type not in SUPPORTED_MEDIA_TYPES:
            return ""
        lines = [
            "An image is attached to this request. Describe what is visible in it."
        ]
        content_type = getattr(image, "contentType", None)
        if content_type:
            lines.append(f"Media type: {content_type}")
        return "\n".join(lines)

    def content_parts(self, deps) -> list:
        from pydantic_ai.messages import ImageUrl

        image = self._image(deps)
        if not self._image_present(image):
            return []
        media_type = (getattr(image, "contentType", "") or "").lower()
        if media_type not in SUPPORTED_MEDIA_TYPES:
            logger.warning("image_content: unsupported media type for multimodal input")
            return []
        data = self._image_data(image)
        if data is None:
            return []
        data, media_type = prepare_image_bytes(data, media_type)
        encoded = base64.b64encode(data).decode("ascii")
        return [
            ImageUrl(
                url=f"data:{media_type};base64,{encoded}",
                media_type=media_type,
            )
        ]


def _raise_invalid_image(message="The submitted image is invalid."):
    raise ImageInputError("invalid_image", message)


def prepare_image_bytes(
    data: bytes,
    media_type: str,
    *,
    strict: bool = False,
) -> tuple[bytes, str]:
    """Verify, orient, and bound image bytes for multimodal model input.

    The legacy persisted-content path remains fail-open when ``strict`` is
    false. Untrusted transient REST input always uses ``strict=True``: decode,
    MIME, dimensions, total pixels, and decompression-bomb checks then fail
    closed and never return unverified original bytes.
    """
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError as exc:  # pragma: no cover
        if strict:
            raise ImageInputError(
                "invalid_image", "Image validation is unavailable."
            ) from exc
        return data, media_type

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(io.BytesIO(data))

        width, height = img.size
        if (
            width < 1
            or height < 1
            or width > MAX_SOURCE_SIDE
            or height > MAX_SOURCE_SIDE
            or width * height > MAX_SOURCE_PIXELS
        ):
            raise ImageInputError(
                "image_too_large",
                "The submitted image dimensions are too large.",
                status=413,
            )

        detected_format = (img.format or "").upper()
        if strict and detected_format not in MEDIA_TYPE_FORMATS.get(media_type, ()):
            _raise_invalid_image("Image content does not match its media type.")

        img.load()
        orientation = None
        try:
            orientation = img.getexif().get(274)
        except (AttributeError, KeyError, TypeError, ValueError):
            pass
        img = ImageOps.exif_transpose(img)

        can_reuse_jpeg = (
            media_type == "image/jpeg"
            and detected_format == "JPEG"
            and len(data) <= NO_REENCODE_MAX_BYTES
            and max(img.size) <= MAX_SIDE
            and img.mode in ("RGB", "L")
            and orientation in (None, 1)
        )
        if can_reuse_jpeg:
            return data, media_type

        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        if max(img.size) > MAX_SIDE:
            img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=JPEG_QUALITY)
        return buffer.getvalue(), "image/jpeg"
    except ImageInputError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
    ) as exc:
        if strict:
            raise ImageInputError(
                "invalid_image", "The submitted image could not be validated."
            ) from exc
        logger.warning("image_content: preparation failed; using original bytes")
        return data, media_type
    except Exception as exc:
        if strict:
            raise ImageInputError(
                "invalid_image", "The submitted image could not be validated."
            ) from exc
        logger.warning("image_content: preparation failed; using original bytes")
        return data, media_type


def decode_transient_image(payload) -> TransientImage:
    """Validate a JSON image payload and return verified in-memory bytes."""
    if not isinstance(payload, dict):
        raise ImageInputError("invalid_request", "An image payload is required.")

    data = payload.get("data")
    encoding = payload.get("encoding")
    media_type = payload.get("content-type")
    filename = payload.get("filename") or "upload"

    if not isinstance(data, str) or not data:
        raise ImageInputError("invalid_request", "Image data is required.")
    if encoding != "base64":
        raise ImageInputError("invalid_request", "Image encoding must be base64.")
    if not isinstance(media_type, str):
        raise ImageInputError("invalid_request", "Image media type is required.")
    media_type = media_type.lower().strip()
    if media_type not in SUPPORTED_MEDIA_TYPES:
        raise ImageInputError(
            "unsupported_media_type",
            "This image format cannot be analysed.",
            status=415,
        )
    if len(data) > MAX_ENCODED_IMAGE_BYTES:
        raise ImageInputError(
            "image_too_large",
            "The submitted image is too large.",
            status=413,
        )
    if not isinstance(filename, str) or len(filename) > 255:
        raise ImageInputError("invalid_request", "Image filename is invalid.")

    try:
        decoded = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError, TypeError) as exc:
        raise ImageInputError(
            "invalid_request", "Image data is not valid base64."
        ) from exc
    if not decoded:
        raise ImageInputError("invalid_request", "Image data is empty.")
    if len(decoded) > MAX_IMAGE_BYTES:
        raise ImageInputError(
            "image_too_large",
            "The submitted image is too large.",
            status=413,
        )

    prepared, prepared_type = prepare_image_bytes(
        decoded,
        media_type,
        strict=True,
    )
    return TransientImage(
        data=prepared,
        contentType=prepared_type,
        filename=filename,
    )


def context_from_existing_image(context) -> TransientImageContext:
    """Create a strict in-memory agent context from a persisted Image."""
    image = getattr(context, "image", None)
    data = _read_image_data(image)
    media_type = (getattr(image, "contentType", "") or "").lower()
    if media_type not in SUPPORTED_MEDIA_TYPES:
        raise ImageInputError(
            "unsupported_media_type",
            "This image format cannot be analysed.",
            status=415,
        )
    if data is None:
        _raise_invalid_image("The Image has no readable image data.")
    if len(data) > MAX_IMAGE_BYTES:
        raise ImageInputError(
            "image_too_large",
            "The Image is too large to analyse.",
            status=413,
        )
    prepared, prepared_type = prepare_image_bytes(data, media_type, strict=True)
    return TransientImageContext(
        image=TransientImage(
            prepared,
            prepared_type,
            str(getattr(image, "filename", "image")),
        ),
        title=str(getattr(context, "title", "") or ""),
        description=str(getattr(context, "description", "") or ""),
    )
