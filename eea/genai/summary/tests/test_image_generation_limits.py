"""Runtime character limits and bounded, non-truncating Image retries."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from eea.genai.core.errors import AgentDisabled
from eea.genai.summary.generate import generate_image_alt, generate_image_metadata


class TestImageGenerationLimits(unittest.TestCase):
    def setUp(self):
        enabled = patch(
            "eea.genai.summary.settings.is_image_ai_enabled", return_value=True
        )
        enabled.start()
        self.addCleanup(enabled.stop)
        executor = patch("eea.genai.summary.generate.get_executor")
        self.executor = executor.start().return_value
        self.addCleanup(executor.stop)
        context = patch("eea.genai.summary.generate.context_from_existing_image")
        context.start().return_value = SimpleNamespace()
        self.addCleanup(context.stop)
        self.image = SimpleNamespace(filename="upload.jpg")

    def test_shared_64_character_limit_retries_title_and_alt(self):
        self.executor.run_with_agent.side_effect = [
            {"title": "x" * 65, "description": "A bird stands among reeds."},
            {"title": "A heron", "description": "A bird stands among reeds."},
            {"alt": "A " + "x" * 64 + "."},
            {"alt": "A heron stands among reeds."},
        ]
        self.assertEqual(generate_image_metadata(self.image, None)["title"], "A heron")
        self.assertEqual(
            generate_image_alt(self.image, None)["alt"], "A heron stands among reeds."
        )
        self.assertEqual(self.executor.run_with_agent.call_count, 4)
        for call in self.executor.run_with_agent.call_args_list:
            self.assertIn("64 characters", call.kwargs["user_prompt"])

    def test_description_limit_retries_both_fields_atomically(self):
        self.executor.run_with_agent.side_effect = [
            {"title": "First title", "description": "x" * 500 + "."},
            {"title": "Replacement title", "description": "A bird stands among reeds."},
        ]
        self.assertEqual(
            generate_image_metadata(self.image, None),
            {"title": "Replacement title", "description": "A bird stands among reeds."},
        )
        self.assertIn(
            "500 characters",
            self.executor.run_with_agent.call_args.kwargs["user_prompt"],
        )

    def test_second_oversized_result_fails_without_truncation(self):
        self.executor.run_with_agent.return_value = {"alt": "A " + "x" * 64 + "."}
        with self.assertRaises(ValueError):
            generate_image_alt(self.image, None)
        self.assertEqual(self.executor.run_with_agent.call_count, 2)

    def test_configured_limits_can_exceed_old_hardcoded_limits(self):
        self.executor.run_with_agent.return_value = {
            "title": "x" * 140,
            "description": "x" * 550 + ".",
        }
        with patch(
            "eea.genai.summary.generate.get_image_ai_limits", return_value=(160, 600)
        ):
            result = generate_image_metadata(self.image, None)
        self.assertEqual(len(result["title"]), 140)
        self.assertEqual(len(result["description"]), 551)
        self.executor.run_with_agent.assert_called_once()

    def test_direct_generation_cannot_bypass_disabled_setting(self):
        with patch(
            "eea.genai.summary.settings.is_image_ai_enabled", return_value=False
        ):
            with self.assertRaises(AgentDisabled):
                generate_image_metadata(self.image, None)
            with self.assertRaises(AgentDisabled):
                generate_image_alt(self.image, None)
        self.executor.run_with_agent.assert_not_called()
