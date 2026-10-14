"""Contracts for structured Image AI output."""

import unittest

from pydantic import ValidationError


class TestImageMetadataResult(unittest.TestCase):
    def _model(self):
        from eea.genai.summary.models import ImageMetadataResult

        return ImageMetadataResult

    def test_normalizes_valid_title_and_description(self):
        result = self._model()(
            title="  Grey heron among reeds  ",
            description="  A grey heron stands in shallow water.  ",
        )

        self.assertEqual(result.title, "Grey heron among reeds")
        self.assertEqual(
            result.description,
            "A grey heron stands in shallow water.",
        )

    def test_rejects_blank_title_atomically(self):
        with self.assertRaises(ValidationError):
            self._model()(title="   ", description="A complete description.")

    def test_rejects_blank_description_atomically(self):
        with self.assertRaises(ValidationError):
            self._model()(title="Grey heron", description="   ")

    def test_structural_models_do_not_override_runtime_character_limits(self):
        result = self._model()(title="x" * 126, description="x" * 501 + ".")
        self.assertEqual(len(result.title), 126)
        self.assertEqual(len(result.description), 502)

    def test_rejects_non_plain_or_invalid_metadata_text(self):
        for title, description in (
            (
                "[AI Generated description] Grey heron",
                "A complete description.",
            ),
            (
                "Grey heron",
                "A bird. [End of AI Generated description]",
            ),
            ("**Grey heron**", "A complete description."),
            ("*Grey heron*", "A complete description."),
            ("AI: Grey heron", "A complete description."),
            ("Image: Grey heron", "A complete description."),
            ("Grey heron", "fragment without sentence punctuation"),
            ("Grey\nheron", "A complete description."),
            ("Grey heron", "One. Two. Three."),
        ):
            with self.subTest(title=title, description=description):
                with self.assertRaises(ValidationError):
                    self._model()(title=title, description=description)


class TestImageAltResult(unittest.TestCase):
    def _model(self):
        from eea.genai.summary.models import ImageAltResult

        return ImageAltResult

    def test_normalizes_valid_alt(self):
        result = self._model()(alt="  A grey heron stands among reeds.  ")
        self.assertEqual(result.alt, "A grey heron stands among reeds.")

    def test_rejects_blank_alt(self):
        with self.assertRaises(ValidationError):
            self._model()(alt="   ")

    def test_structural_model_allows_configurable_alt_limits(self):
        result = self._model()(alt="x" * 126 + ".")
        self.assertEqual(len(result.alt), 127)

    def test_rejects_non_plain_label_or_non_sentence_alt(self):
        for alt in (
            "[AI Generated description] A grey heron.",
            "Image of a grey heron.",
            "**A grey heron.**",
            "A grey heron without punctuation",
            "One sentence. A second sentence.",
        ):
            with self.subTest(alt=alt):
                with self.assertRaises(ValidationError):
                    self._model()(alt=alt)


if __name__ == "__main__":
    unittest.main()
