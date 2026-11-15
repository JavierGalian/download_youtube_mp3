"""Focused tests for agent validation, retries, and workspace cleanup."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from youtube_mp3.agent import DownloadAgent
from youtube_mp3.exceptions import (
    FFmpegError,
    GeoRestrictedError,
    InvalidURLError,
    NetworkError,
)
from youtube_mp3.file_manager import FileManager
from youtube_mp3.media_processor import MediaProcessor
from youtube_mp3.youtube_processor import YouTubeProcessor


class FakeProcessor(MediaProcessor):
    def __init__(self, failures: int = 0) -> None:
        self.failures = failures
        self.workspaces: list[Path] = []

    def process(self, url: str, working_directory: Path) -> Path:
        self.workspaces.append(working_directory)
        if self.failures:
            self.failures -= 1
            (working_directory / "partial.tmp").write_text("partial")
            raise NetworkError("temporary network failure")
        output = working_directory / "audio.mp3"
        output.write_bytes(b"mp3")
        return output


class DownloadAgentTests(unittest.TestCase):
    def test_reports_missing_ffmpeg_before_download(self) -> None:
        with patch("youtube_mp3.youtube_processor.shutil.which", return_value=None):
            with self.assertRaises(FFmpegError):
                YouTubeProcessor().process(
                    "https://youtu.be/example", Path(".")
                )

    def test_accepts_ffmpeg_executable_found_on_path(self) -> None:
        for executable in (r"C:\tools\ffmpeg.exe", "/usr/bin/ffmpeg"):
            with self.subTest(executable=executable):
                with patch(
                    "youtube_mp3.youtube_processor.shutil.which",
                    return_value=executable,
                ) as which_mock:
                    self.assertEqual(
                        YouTubeProcessor._require_ffmpeg(), executable
                    )
                which_mock.assert_called_once_with("ffmpeg")

    def test_translates_country_block_to_geographic_error(self) -> None:
        translated = YouTubeProcessor._translate_download_error(
            Exception("This video is not available in your country")
        )

        self.assertIsInstance(translated, GeoRestrictedError)

    def test_retries_network_failure_and_cleans_workspaces(self) -> None:
        with tempfile.TemporaryDirectory() as output_directory:
            processor = FakeProcessor(failures=1)
            agent = DownloadAgent(
                processor, FileManager(output_directory), retries=1, retry_delay_seconds=0
            )

            result = agent.download("https://www.youtube.com/watch?v=example")

            self.assertEqual(result.read_bytes(), b"mp3")
            self.assertEqual(len(processor.workspaces), 2)
            self.assertTrue(all(not path.exists() for path in processor.workspaces))
            self.assertEqual(
                [path.name for path in Path(output_directory).iterdir()],
                ["audio.mp3"],
            )

    def test_rejects_malformed_url_before_processing(self) -> None:
        with tempfile.TemporaryDirectory() as output_directory:
            processor = FakeProcessor()
            agent = DownloadAgent(processor, FileManager(output_directory))

            with self.assertRaises(InvalidURLError):
                agent.download("file:///private/video.mp4")

            self.assertEqual(processor.workspaces, [])

    def test_cancellation_cleans_temporary_workspace(self) -> None:
        class InterruptingProcessor(FakeProcessor):
            def process(self, url: str, working_directory: Path) -> Path:
                self.workspaces.append(working_directory)
                (working_directory / "partial.tmp").write_text("partial")
                raise KeyboardInterrupt

        with tempfile.TemporaryDirectory() as output_directory:
            processor = InterruptingProcessor()
            agent = DownloadAgent(processor, FileManager(output_directory))

            with self.assertRaises(KeyboardInterrupt):
                agent.download("https://youtu.be/example")

            self.assertTrue(all(not path.exists() for path in processor.workspaces))
