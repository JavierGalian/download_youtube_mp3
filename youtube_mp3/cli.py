"""Command-line interface for the YouTube-to-MP3 application."""

import argparse
import os
import sys
from pathlib import Path

from .agent import DownloadAgent
from .exceptions import MediaDownloadError
from .file_manager import FileManager
from .youtube_processor import YouTubeProcessor


def default_output_directory() -> str:
    """Choose the default music directory for desktop or Termux/Android."""
    home_directory = Path.home()
    shared_music_directory = home_directory / "storage" / "shared" / "Music"
    termux_prefix = os.environ.get("PREFIX", "").casefold()
    is_termux = (
        "TERMUX_VERSION" in os.environ
        or "com.termux" in termux_prefix
        or shared_music_directory.is_dir()
    )
    if is_termux:
        return "~/storage/shared/Music/YouTube MP3"
    return "~/Music/YouTube MP3"


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="youtube-mp3",
        description=(
            "Download and convert audio from a YouTube video you own or are "
            "authorized to download."
        ),
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="URL of the YouTube video (prompted if omitted)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=default_output_directory(),
        help="destination directory (default: %(default)s)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="number of retries after transient network failures (default: %(default)s)",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="initial retry delay in seconds; subsequent delays double",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.retries < 0:
        parser.error("--retries must be zero or greater")
    if arguments.retry_delay < 0:
        parser.error("--retry-delay must be zero or greater")

    url = arguments.url
    if url is None:
        try:
            url = input("Ingresa la URL de YouTube: ")
        except KeyboardInterrupt:
            print("\nEntrada cancelada.", file=sys.stderr)
            return 130
        except EOFError:
            print("\nNo se recibió una URL.", file=sys.stderr)
            return 1

    agent = DownloadAgent(
        processor=YouTubeProcessor(),
        file_manager=FileManager(Path(arguments.output)),
        retries=arguments.retries,
        retry_delay_seconds=arguments.retry_delay,
    )
    try:
        output_path = agent.download(url)
    except KeyboardInterrupt:
        print("\nDownload cancelled; temporary files were removed.", file=sys.stderr)
        return 130
    except MediaDownloadError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"File system error: {error}", file=sys.stderr)
        return 1

    print(f"MP3 saved to: {output_path}")
    return 0
