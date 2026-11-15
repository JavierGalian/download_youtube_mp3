"""Filesystem operations and temporary workspace management."""

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class FileManager:
    """Manage destination directories and isolated temporary workspaces."""

    def __init__(self, output_directory: str | Path) -> None:
        """Expand a user-relative path and prepare its destination directory."""
        self.output_directory = Path(
            os.path.expanduser(os.fspath(output_directory))
        ).resolve()

    def ensure_output_directory(self) -> None:
        """Create the output directory if it does not already exist."""
        self.output_directory.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def temporary_workspace(self) -> Iterator[Path]:
        """Yield an isolated workspace that is removed on every exit path."""
        self.ensure_output_directory()
        with tempfile.TemporaryDirectory(
            prefix=".youtube-mp3-", dir=self.output_directory
        ) as temporary_directory:
            yield Path(temporary_directory)

    def publish(self, source: Path) -> Path:
        """Move a completed audio file into the output directory.

        ``os.replace`` makes the final move atomic on the same filesystem.
        A repeated download with the same output name replaces the prior file.
        """
        self.ensure_output_directory()
        if not source.is_file():
            raise FileNotFoundError(f"Converted audio file was not created: {source}")
        destination = self.output_directory / source.name
        os.replace(source, destination)
        return destination

    def remove_file(self, path: Path) -> None:
        """Remove a file if it exists, without hiding other filesystem errors."""
        if path.is_file():
            path.unlink()

    def remove_tree(self, path: Path) -> None:
        """Remove a directory tree if it exists."""
        if path.is_dir():
            shutil.rmtree(path)
