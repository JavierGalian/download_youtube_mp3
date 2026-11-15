"""YouTube-specific download and FFmpeg conversion adapter."""

import shutil
from pathlib import Path
from typing import Any

from .exceptions import (
    DependencyError,
    FFmpegError,
    GeoRestrictedError,
    InvalidURLError,
    MediaProcessorError,
    NetworkError,
    VideoUnavailableError,
)
from .media_processor import MediaProcessor


class YouTubeProcessor(MediaProcessor):
    """Download a YouTube video's audio and convert it to MP3 with FFmpeg."""

    _NETWORK_MARKERS = (
        "timed out",
        "timeout",
        "connection reset",
        "connection aborted",
        "temporary failure in name resolution",
        "name or service not known",
        "network is unreachable",
        "unable to download webpage",
        "http error 429",
        "http error 5",
    )
    _FFMPEG_MARKERS = (
        "ffmpeg not found",
        "ffprobe not found",
        "ffmpeg is not installed",
        "postprocessing",
        "ffmpeg",
    )
    _PRIVATE_MARKERS = ("private video", "members-only", "members only")
    _GEO_MARKERS = (
        "not available in your country",
        "not available in your region",
        "geo-restricted",
        "georestricted",
    )
    _UNAVAILABLE_MARKERS = (
        "video unavailable",
        "has been removed",
        "this video is unavailable",
        "sign in to confirm",
    )

    def process(self, url: str, working_directory: Path) -> Path:
        """Fetch ``url`` and return the converted MP3 inside the workspace."""
        try:
            import yt_dlp
        except ImportError as error:
            raise DependencyError(
                "yt-dlp is required. Install project dependencies with "
                "'python -m pip install -r requirements.txt'."
            ) from error

        try:
            from yt_dlp.postprocessor.ffmpeg import FFmpegPostProcessorError
            from yt_dlp.utils import (
                DownloadError,
                ExtractorError,
                GeoRestrictedError as YtDlpGeoRestrictedError,
                UnavailableVideoError,
            )
        except ImportError as error:
            raise DependencyError(
                "yt-dlp is installed but its required modules could not be loaded. "
                "Try reinstalling it with 'python -m pip install --upgrade yt-dlp'."
            ) from error

        self._require_ffmpeg()

        options: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": str(working_directory / "%(title).200B [%(id)s].%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "continuedl": False,
            "nopart": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(url, download=True)
                if not isinstance(info, dict):
                    raise MediaProcessorError(
                        "yt-dlp did not return video information."
                    )
                output_path = Path(downloader.prepare_filename(info)).with_suffix(
                    ".mp3"
                )
                if not output_path.is_file():
                    raise MediaProcessorError(
                        "FFmpeg finished without producing the expected MP3 file."
                    )
                return output_path
        except YtDlpGeoRestrictedError as error:
            raise GeoRestrictedError(
                "This video is not available in your region."
            ) from error
        except UnavailableVideoError as error:
            raise VideoUnavailableError(
                "This video is unavailable or cannot be accessed."
            ) from error
        except FFmpegPostProcessorError as error:
            raise FFmpegError(
                "FFmpeg conversion failed. Check that FFmpeg is installed and "
                "available on PATH."
            ) from error
        except (ExtractorError, DownloadError) as error:
            raise self._translate_download_error(error) from error

    @staticmethod
    def _require_ffmpeg() -> str:
        """Return the FFmpeg executable found on PATH or raise a clear error."""
        executable = shutil.which("ffmpeg")
        if executable is None:
            raise FFmpegError(
                "FFmpeg was not found on PATH. Install FFmpeg and make sure it "
                "is available as 'ffmpeg' (or 'ffmpeg.exe' on Windows)."
            )
        return executable

    @classmethod
    def _translate_download_error(cls, error: Exception) -> Exception:
        """Translate yt-dlp's less-specific errors to actionable messages."""
        message = str(error)
        normalized = message.casefold()

        if any(marker in normalized for marker in cls._PRIVATE_MARKERS):
            return VideoUnavailableError(
                "This video is private or requires channel membership."
            )
        if any(marker in normalized for marker in cls._GEO_MARKERS) or (
            "geo" in normalized
            and ("restrict" in normalized or "country" in normalized or "region" in normalized)
        ):
            return GeoRestrictedError("This video is not available in your region.")
        if any(marker in normalized for marker in cls._UNAVAILABLE_MARKERS):
            return VideoUnavailableError(
                "This video is unavailable or cannot be accessed."
            )
        if any(marker in normalized for marker in cls._FFMPEG_MARKERS):
            return FFmpegError(
                "FFmpeg conversion failed. Check that FFmpeg is installed and "
                "available on PATH."
            )
        if any(marker in normalized for marker in cls._NETWORK_MARKERS):
            return NetworkError(
                "A temporary network error occurred while downloading the video."
            )
        if (
            "unsupported url" in normalized
            or "url is not supported" in normalized
            or "not a valid url" in normalized
        ):
            return InvalidURLError(
                "The URL is not supported. Provide a valid YouTube video URL."
            )
        return MediaProcessorError(f"yt-dlp failed: {message}")
