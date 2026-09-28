"""Unit tests for the multimodal ImageContentProvider (no Plone bootstrap)."""

import io
import unittest
from types import SimpleNamespace

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
        ctx = SimpleNamespace(
            image=_FakeImage(_make_jpeg(), filename="amenda.jpeg")
        )
        parts = self.provider.content_parts(_Deps(context=ctx))
        self.assertEqual(len(parts), 1)
        self.assertTrue(parts[0].url.startswith("data:image/jpeg;base64,"))
        self.assertEqual(parts[0].media_type, "image/jpeg")

    def test_unsupported_media_type_skipped(self):
        ctx = SimpleNamespace(
            image=_FakeImage(b"%PDF-1.4", content_type="application/pdf")
        )
        self.assertEqual(self.provider.content_parts(_Deps(context=ctx)), [])

    def test_user_prompt_describes_image(self):
        ctx = SimpleNamespace(
            image=_FakeImage(_make_jpeg(), filename="amenda.jpeg")
        )
        text = self.provider.user_prompt(_Deps(context=ctx))
        self.assertIn("amenda.jpeg", text)
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


class TestImageSummarizerAgentConfig(unittest.TestCase):
    def test_config_values(self):
        from eea.genai.summary.agents import ImageSummarizerAgent

        cfg = ImageSummarizerAgent().config
        self.assertEqual(cfg["name"], "summarizer:Image")
        self.assertIn("image_content", cfg["enrichers"])
        self.assertIn("generic_metadata_no_dates", cfg["enrichers"])
        self.assertTrue(cfg["summary_markers"])
        self.assertEqual(cfg["max_summary_length"], 125)
        self.assertIn("one", cfg["task_prompt"].lower())
        self.assertIn("125", cfg["task_prompt"])

    def test_plain_summarizer_has_no_markers(self):
        from eea.genai.summary.agents import SummarizerAgent

        self.assertFalse(SummarizerAgent().config.get("summary_markers", False))
        self.assertNotIn("max_summary_length", SummarizerAgent().config)
