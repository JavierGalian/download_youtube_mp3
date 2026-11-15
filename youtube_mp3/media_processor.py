"""Abstraction for media processors that can be supplied to the agent."""

from abc import ABC, abstractmethod
from pathlib import Path


class MediaProcessor(ABC):
    """Process a media URL into an audio file in a temporary directory.

    Implementations own platform-specific download and conversion behavior.
    They should return the path to the completed audio file and leave temporary
    artifact cleanup to the caller's workspace manager.
    """

    @abstractmethod
    def process(self, url: str, working_directory: Path) -> Path:
        """Download and convert ``url``, returning the resulting audio path."""
        raise NotImplementedError
