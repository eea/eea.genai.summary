"""Multimodal image content provider.

Attaches the actual image bytes of an Image content object to the agent's
user prompt as a pydantic_ai ``ImageUrl`` part, so the LLM sees the image
itself instead of metadata only (issue #305021).
"""

from __future__ import annotations

import base64
import io
import logging

from eea.genai.core.interfaces import Enricher

logger = logging.getLogger("eea.genai.summary")

#: Media types the LLM gateway accepts for image input.
SUPPORTED_MEDIA_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}
)

#: Max image side (px) sent to the model. Larger images are downscaled.
MAX_SIDE = 2048

#: JPEG quality used when re-encoding after a downscale.
JPEG_QUALITY = 85

#: Images smaller than this (bytes) are sent as-is without re-encoding.
NO_REENCODE_MAX_BYTES = 1_000_000


class ImageContentProvider(Enricher):
    """Enricher that feeds the content's primary image to the model.

    Expects ``deps.context`` to expose a named image value (e.g. the
    ``image`` field of a Plone ``Image`` content type) supporting
    ``getData()`` / ``contentType`` / ``filename``.
    """

    name = "image_content"
    description = "Attaches the image bytes of Image content to the prompt"

    image_field = "image"

    def _image(self, deps):
        context = getattr(deps, "context", None)
        if context is None:
            return None
        return getattr(context, self.image_field, None)

    def _image_data(self, image):
        if image is None:
            return None
        try:
            # plone.namedfile: NamedFile keeps bytes in the `data` attribute,
            # NamedBlobFile/NamedBlobImage expose it as a property reading
            # the persistent blob (or via the public open() API).
            data = getattr(image, "data", None)
            if data is None:
                open_fn = getattr(image, "open", None)
                if callable(open_fn):
                    with open_fn("r") as fp:
                        data = fp.read()
        except Exception:
            logger.exception("image_content: failed to read image data")
            return None
        if isinstance(data, (bytes, bytearray)):
            return bytes(data) or None
        return None

    def _image_present(self, image) -> bool:
        """Cheap presence check without reading the blob.

        user_prompt() runs on every agent invocation, so it must not pay
        for a full blob read just to test whether an image exists.
        """
        if image is None:
            return False
        size_fn = getattr(image, "getSize", None)
        if callable(size_fn):
            try:
                return bool(size_fn())
            except Exception:
                return False
        # No cheap size accessor (e.g. test doubles) — fall back to data.
        return self._image_data(image) is not None

    def user_prompt(self, deps) -> str:
        image = self._image(deps)
        if not self._image_present(image):
            return ""
        # Stay consistent with content_parts: do not claim an image is
        # attached when its media type will not be sent to the model.
        media_type = (getattr(image, "contentType", "") or "").lower()
        if media_type not in SUPPORTED_MEDIA_TYPES:
            return ""
        lines = [
            "An image is attached to this request. Describe what is visible in it."
        ]
        filename = getattr(image, "filename", None)
        content_type = getattr(image, "contentType", None)
        if filename:
            lines.append(f"File name: {filename}")
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
            logger.warning(
                "image_content: media type %r not supported for LLM image "
                "input; sending metadata only",
                media_type,
            )
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


def prepare_image_bytes(data: bytes, media_type: str) -> tuple[bytes, str]:
    """Downscale/normalize the image so the prompt payload stays bounded.

    Returns ``(bytes, media_type)``. Small JPEGs are returned unchanged;
    other rasters are re-encoded as JPEG; oversized images are downscaled.
    If Pillow is unavailable or decoding fails, the original bytes are
    returned unchanged.
    """
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        return data, media_type

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        if media_type == "image/jpeg" and len(data) <= NO_REENCODE_MAX_BYTES:
            if max(img.size) <= MAX_SIDE:
                return data, media_type
        if max(img.size) > MAX_SIDE:
            img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=JPEG_QUALITY)
        return buffer.getvalue(), "image/jpeg"
    except Exception:
        logger.exception(
            "image_content: failed to prepare image; sending original bytes"
        )
        return data, media_type
