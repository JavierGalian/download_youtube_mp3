"""Application-level exceptions for media downloads."""


class MediaDownloadError(Exception):
    """Base exception for expected download and conversion failures."""


class InvalidURLError(MediaDownloadError):
    """Raised when a supplied URL is malformed or unsupported."""


class VideoUnavailableError(MediaDownloadError):
    """Raised when a video cannot be accessed, including private videos."""


class GeoRestrictedError(MediaDownloadError):
    """Raised when a video is blocked in the current region."""


class NetworkError(MediaDownloadError):
    """Raised for transient network failures that may be retried."""


class FFmpegError(MediaDownloadError):
    """Raised when FFmpeg is missing or media conversion fails."""


class MediaProcessorError(MediaDownloadError):
    """Raised when a processor fails for a reason not covered elsewhere."""


class DependencyError(MediaDownloadError):
    """Raised when a required external Python package is not installed."""
