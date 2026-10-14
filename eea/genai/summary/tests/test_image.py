"""Unit tests for the multimodal ImageContentProvider (no Plone bootstrap)."""

import io
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from eea.genai.summary.image import (
    ImageContentProvider,
    prepare_image_bytes,
)


def _make_jpeg(size=(800, 600), color=(200, 30, 30)):
    from PIL import Image

    img = Image.new("RGB", size, color)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def _make_png(size=(40, 40)):
    from PIL import Image

    img = Image.new("RGBA", size, (30, 200, 30, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class _FakeImage:
    def __init__(self, data, content_type="image/jpeg", filename="x.jpeg"):
        self.data = data
        self.contentType = content_type
        self.filename = filename

    def getSize(self):
        return len(self.data) if self.data else 0


class _Deps:
    def __init__(self, context=None):
        self.context = context


class TestImageContentProviderParts(unittest.TestCase):
    def setUp(self):
        self.provider = ImageContentProvider()

    def test_no_context_returns_empty(self):
        self.assertEqual(self.provider.content_parts(_Deps(context=None)), [])

    def test_context_without_image_returns_empty(self):
        self.assertEqual(
            self.provider.content_parts(_Deps(context=SimpleNamespace())), []
        )

    def test_empty_image_data_returns_empty(self):
        ctx = SimpleNamespace(image=_FakeImage(b""))
        self.assertEqual(self.provider.content_parts(_Deps(context=ctx)), [])

    def test_jpeg_returns_data_url_part(self):
        ctx = SimpleNamespace(image=_FakeImage(_make_jpeg(), filename="amenda.jpeg"))
        parts = self.provider.content_parts(_Deps(context=ctx))
        self.assertEqual(len(parts), 1)
        self.assertTrue(parts[0].url.startswith("data:image/jpeg;base64,"))
        self.assertEqual(parts[0].media_type, "image/jpeg")

    def test_unsupported_media_type_skipped(self):
        ctx = SimpleNamespace(
            image=_FakeImage(b"%PDF-1.4", content_type="application/pdf")
        )
        self.assertEqual(self.provider.content_parts(_Deps(context=ctx)), [])

    def test_user_prompt_describes_image_without_exposing_filename(self):
        ctx = SimpleNamespace(image=_FakeImage(_make_jpeg(), filename="amenda.jpeg"))
        text = self.provider.user_prompt(_Deps(context=ctx))
        self.assertNotIn("amenda.jpeg", text)
        self.assertIn("image/jpeg", text)
        self.assertIn("visible", text)

    def test_user_prompt_empty_without_image(self):
        self.assertEqual(
            self.provider.user_prompt(_Deps(context=SimpleNamespace())), ""
        )

    def test_user_prompt_empty_for_unsupported_media(self):
        ctx = SimpleNamespace(
            image=_FakeImage(b"%PDF-1.4", content_type="application/pdf")
        )
        self.assertEqual(self.provider.user_prompt(_Deps(context=ctx)), "")

    def test_user_prompt_empty_for_empty_image(self):
        ctx = SimpleNamespace(image=_FakeImage(b""))
        self.assertEqual(self.provider.user_prompt(_Deps(context=ctx)), "")

    def test_data_error_returns_empty(self):
        class _Broken:
            contentType = "image/jpeg"
            filename = "x.jpg"

            @property
            def data(self):
                raise RuntimeError("blob gone")

        ctx = SimpleNamespace(image=_Broken())
        self.assertEqual(self.provider.content_parts(_Deps(context=ctx)), [])
        self.assertEqual(self.provider.user_prompt(_Deps(context=ctx)), "")


class TestPrepareImageBytes(unittest.TestCase):
    def test_small_jpeg_untouched(self):
        data = _make_jpeg()
        out, media = prepare_image_bytes(data, "image/jpeg")
        self.assertEqual(out, data)
        self.assertEqual(media, "image/jpeg")

    def test_oversized_jpeg_downscaled(self):
        data = _make_jpeg(size=(4000, 3000))
        out, media = prepare_image_bytes(data, "image/jpeg")
        from PIL import Image

        img = Image.open(io.BytesIO(out))
        self.assertLessEqual(max(img.size), 2048)
        self.assertEqual(media, "image/jpeg")
        self.assertLess(len(out), len(data))

    def test_png_reencoded_as_jpeg(self):
        data = _make_png()
        out, media = prepare_image_bytes(data, "image/png")
        self.assertEqual(media, "image/jpeg")
        self.assertNotEqual(out, data)

    def test_undecodable_bytes_returned_unchanged(self):
        data = b"not-an-image"
        out, media = prepare_image_bytes(data, "image/jpeg")
        self.assertEqual(out, data)
        self.assertEqual(media, "image/jpeg")

    def test_strict_mode_rejects_undecodable_bytes_without_fallback(self):
        from eea.genai.summary.image import ImageInputError

        with self.assertRaises(ImageInputError) as raised:
            prepare_image_bytes(b"not-an-image", "image/jpeg", strict=True)

        self.assertEqual(raised.exception.code, "invalid_image")

    def test_strict_mode_rejects_excessive_dimensions_before_load(self):
        from eea.genai.summary.image import MAX_SOURCE_SIDE, ImageInputError

        fake = Mock()
        fake.size = (MAX_SOURCE_SIDE + 1, 1)
        with patch("PIL.Image.open", return_value=fake):
            with self.assertRaises(ImageInputError) as raised:
                prepare_image_bytes(b"header", "image/png", strict=True)

        self.assertEqual(raised.exception.code, "image_too_large")
        fake.load.assert_not_called()

    def test_strict_mode_rejects_excessive_total_pixels_before_load(self):
        from eea.genai.summary.image import (
            MAX_SOURCE_PIXELS,
            MAX_SOURCE_SIDE,
            ImageInputError,
        )

        width = MAX_SOURCE_SIDE
        height = (MAX_SOURCE_PIXELS // width) + 1
        self.assertLessEqual(height, MAX_SOURCE_SIDE)
        fake = Mock()
        fake.size = (width, height)
        with patch("PIL.Image.open", return_value=fake):
            with self.assertRaises(ImageInputError) as raised:
                prepare_image_bytes(b"header", "image/png", strict=True)

        self.assertEqual(raised.exception.code, "image_too_large")
        fake.load.assert_not_called()

    def test_strict_mode_rejects_decompression_bomb_error(self):
        from PIL import Image

        from eea.genai.summary.image import ImageInputError

        with patch(
            "PIL.Image.open",
            side_effect=Image.DecompressionBombError("too many pixels"),
        ):
            with self.assertRaises(ImageInputError) as raised:
                prepare_image_bytes(b"header", "image/png", strict=True)

        self.assertEqual(raised.exception.code, "invalid_image")

    def test_strict_mode_rejects_decompression_bomb_warning(self):
        import warnings

        from PIL import Image

        from eea.genai.summary.image import ImageInputError

        def warn_on_open(*args, **kwargs):
            warnings.warn("too many pixels", Image.DecompressionBombWarning)
            return Mock(size=(100, 100))

        with patch("PIL.Image.open", side_effect=warn_on_open):
            with self.assertRaises(ImageInputError) as raised:
                prepare_image_bytes(b"header", "image/png", strict=True)

        self.assertEqual(raised.exception.code, "invalid_image")

    def test_oversized_encoded_payload_is_rejected_before_base64_decode(self):
        from eea.genai.summary.image import (
            MAX_ENCODED_IMAGE_BYTES,
            ImageInputError,
            decode_transient_image,
        )

        payload = {
            "data": "A" * (MAX_ENCODED_IMAGE_BYTES + 1),
            "encoding": "base64",
            "content-type": "image/png",
            "filename": "large.png",
        }
        with patch("eea.genai.summary.image.base64.b64decode") as decode:
            with self.assertRaises(ImageInputError) as raised:
                decode_transient_image(payload)

        self.assertEqual(raised.exception.code, "image_too_large")
        decode.assert_not_called()

    def test_transient_decoder_rejects_empty_decoded_bytes(self):
        from eea.genai.summary.image import ImageInputError, decode_transient_image

        with self.assertRaises(ImageInputError) as raised:
            decode_transient_image(
                {
                    "data": "",
                    "encoding": "base64",
                    "content-type": "image/png",
                    "filename": "empty.png",
                }
            )

        self.assertEqual(raised.exception.code, "invalid_request")

    def test_transient_decoder_accepts_every_supported_format(self):
        import base64

        from PIL import Image, features

        from eea.genai.summary.image import decode_transient_image

        formats = (
            ("JPEG", "image/jpeg", "RGB"),
            ("PNG", "image/png", "RGBA"),
            ("WEBP", "image/webp", "RGB"),
            ("GIF", "image/gif", "P"),
            ("BMP", "image/bmp", "RGB"),
        )
        for image_format, media_type, mode in formats:
            if image_format == "WEBP" and not features.check("webp"):
                continue
            with self.subTest(image_format=image_format):
                image = Image.new(mode, (8, 8))
                output = io.BytesIO()
                image.save(output, format=image_format)
                result = decode_transient_image(
                    {
                        "data": base64.b64encode(output.getvalue()).decode("ascii"),
                        "encoding": "base64",
                        "content-type": media_type,
                        "filename": f"image.{image_format.lower()}",
                    }
                )

                self.assertTrue(result.data)
                self.assertEqual(result.contentType, "image/jpeg")

    def test_exif_orientation_is_applied_before_model_input(self):
        from PIL import Image

        image = Image.new("RGB", (20, 10), (100, 20, 30))
        exif = Image.Exif()
        exif[274] = 6
        source = io.BytesIO()
        image.save(source, format="JPEG", exif=exif)

        prepared, media_type = prepare_image_bytes(
            source.getvalue(),
            "image/jpeg",
            strict=True,
        )
        result = Image.open(io.BytesIO(prepared))

        self.assertEqual(result.size, (10, 20))
        self.assertEqual(media_type, "image/jpeg")

    def test_transient_decoder_rejects_mime_content_mismatch(self):
        from eea.genai.summary.image import ImageInputError, decode_transient_image

        import base64

        payload = {
            "data": base64.b64encode(_make_png(size=(8, 8))).decode("ascii"),
            "encoding": "base64",
            "content-type": "image/jpeg",
            "filename": "mismatch.jpg",
        }

        with self.assertRaises(ImageInputError) as raised:
            decode_transient_image(payload)

        self.assertEqual(raised.exception.code, "invalid_image")


class TestImageAgentConfig(unittest.TestCase):
    def test_metadata_agent_uses_structured_plain_output(self):
        from eea.genai.summary.agents import ImageMetadataAgent

        cfg = ImageMetadataAgent().config
        self.assertEqual(cfg["name"], "image_metadata")
        self.assertEqual(cfg["enrichers"], ["image_content"])
        self.assertEqual(
            cfg["output_type"],
            "eea.genai.summary.models.ImageMetadataResult",
        )
        self.assertFalse(cfg.get("summary_markers", False))

    def test_alt_agent_uses_image_and_metadata(self):
        from eea.genai.summary.agents import ImageAltAgent

        cfg = ImageAltAgent().config
        self.assertEqual(cfg["name"], "image_alt")
        self.assertIn("image_content", cfg["enrichers"])
        self.assertIn("generic_metadata_no_dates", cfg["enrichers"])
        self.assertEqual(
            cfg["output_type"],
            "eea.genai.summary.models.ImageAltResult",
        )
        self.assertFalse(cfg.get("summary_markers", False))

    def test_plain_summarizer_has_no_markers(self):
        from eea.genai.summary.agents import SummarizerAgent

        self.assertFalse(SummarizerAgent().config.get("summary_markers", False))
        self.assertNotIn("max_summary_length", SummarizerAgent().config)
