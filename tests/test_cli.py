"""Tests for interactive CLI input and platform-specific output defaults."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from youtube_mp3 import cli


class CliTests(unittest.TestCase):
    def test_prompts_for_url_when_no_argument_is_provided(self) -> None:
        expected_output = Path("audio.mp3")
        with (
            patch("builtins.input", return_value="https://youtu.be/example") as input_mock,
            patch("youtube_mp3.cli.DownloadAgent") as agent_class,
        ):
            agent_class.return_value.download.return_value = expected_output

            result = cli.main([])

        self.assertEqual(result, 0)
        input_mock.assert_called_once_with("Ingresa la URL de YouTube: ")
        agent_class.return_value.download.assert_called_once_with(
            "https://youtu.be/example"
        )

    def test_defaults_to_termux_shared_music_path(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            with (
                patch.dict("os.environ", {"TERMUX_VERSION": "0.118"}),
                patch("youtube_mp3.cli.Path.home", return_value=Path(home)),
                patch("youtube_mp3.cli.Path.is_dir", return_value=False),
            ):
                output_directory = cli.default_output_directory()

        self.assertEqual(output_directory, "~/storage/shared/Music/YouTube MP3")

    def test_defaults_to_desktop_music_path(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            with (
                patch.dict("os.environ", {}, clear=True),
                patch("youtube_mp3.cli.Path.home", return_value=Path(home)),
                patch("youtube_mp3.cli.Path.is_dir", return_value=False),
            ):
                output_directory = cli.default_output_directory()

        self.assertEqual(output_directory, "~/Music/YouTube MP3")
