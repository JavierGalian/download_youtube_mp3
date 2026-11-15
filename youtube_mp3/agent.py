"""Application service that coordinates validation, retries, and file handling."""

import time
from pathlib import Path
from urllib.parse import urlsplit

from .exceptions import InvalidURLError, NetworkError
from .file_manager import FileManager
from .media_processor import MediaProcessor


class DownloadAgent:
    """Coordinate a media processor and filesystem manager."""

    def __init__(
        self,
        processor: MediaProcessor,
        file_manager: FileManager,
        retries: int = 2,
        retry_delay_seconds: float = 1.0,
    ) -> None:
        """Configure retry behavior; ``retries`` is the number of extra attempts."""
        if retries < 0:
            raise ValueError("retries must be zero or greater")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be zero or greater")
        self.processor = processor
        self.file_manager = file_manager
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds

    def download(self, url: str) -> Path:
        """Download and publish one audio file, cleaning each attempt's workspace."""
        self._validate_url(url)

        for attempt in range(self.retries + 1):
            try:
                with self.file_manager.temporary_workspace() as workspace:
                    audio_file = self.processor.process(url, workspace)
                    return self.file_manager.publish(audio_file)
            except NetworkError:
                if attempt >= self.retries:
                    raise
                time.sleep(self.retry_delay_seconds * (2**attempt))

        raise RuntimeError("Download retry loop exited unexpectedly.")

    @staticmethod
    def _validate_url(url: str) -> None:
        """Reject malformed or non-web URLs before starting a download."""
        try:
            parsed_url = urlsplit(url.strip())
        except ValueError as error:
            raise InvalidURLError("The provided URL is malformed.") from error
        if (
            parsed_url.scheme not in {"http", "https"}
            or not parsed_url.hostname
        ):
            raise InvalidURLError(
                "Enter a valid YouTube URL beginning with http:// or https://."
            )
