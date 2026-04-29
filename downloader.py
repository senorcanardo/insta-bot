import os
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path to Instagram cookies file (optional but recommended)
COOKIES_FILE = os.environ.get("COOKIES_FILE", "cookies.txt")

# Telegram max file size (50MB in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024


def get_yt_dlp_cmd(url: str, output_dir: str) -> list[str]:
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-o", f"{output_dir}/%(title)s_%(id)s.%(ext)s",
        "--merge-output-format", "mp4",
        "--write-info-json",
        # Tell yt-dlp to also grab images, not just video
        "--extractor-args", "instagram:include_feed_data=1",
        url
    ]
    if os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])
        logger.info("Using cookies file for authentication.")
    else:
        logger.warning("No cookies file found. Public content only.")
    return cmd

    if os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])
        logger.info("Using cookies file for authentication.")
    else:
        logger.warning("No cookies file found. Public content only.")

    return cmd


def download_instagram_media(url: str) -> list[Path]:
    """
    Download media from an Instagram URL.
    Returns a list of downloaded file paths.
    """
    tmp_dir = tempfile.mkdtemp(prefix="instabot_")
    logger.info(f"Downloading {url} to {tmp_dir}")

    cmd = get_yt_dlp_cmd(url, tmp_dir)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"yt-dlp stderr: {result.stderr}")
            raise RuntimeError(f"yt-dlp failed: {result.stderr[-300:]}")

        logger.info(f"yt-dlp stdout: {result.stdout[-300:]}")

    except subprocess.TimeoutExpired:
        raise RuntimeError("Download timed out after 2 minutes.")

    # Collect downloaded media files (exclude .json info files)
    media_extensions = {".mp4", ".mov", ".webm", ".jpg", ".jpeg", ".png", ".webp"}
    files = sorted([
        Path(tmp_dir) / f
        for f in os.listdir(tmp_dir)
        if Path(f).suffix.lower() in media_extensions
    ])

    if not files:
        raise RuntimeError("No media files were downloaded.")

    # Check file sizes
    oversized = [f for f in files if f.stat().st_size > MAX_FILE_SIZE]
    if oversized:
        logger.warning(f"{len(oversized)} file(s) exceed Telegram's 50MB limit and will be skipped.")
        files = [f for f in files if f.stat().st_size <= MAX_FILE_SIZE]

    if not files:
        raise RuntimeError("All downloaded files exceed Telegram's 50MB limit.")

    logger.info(f"Successfully downloaded {len(files)} file(s).")
    return files


def cleanup(files: list[Path]):
    """Remove downloaded files and their temp directory."""
    dirs_to_remove = set()
    for f in files:
        dirs_to_remove.add(f.parent)
        try:
            f.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Could not delete {f}: {e}")

    for d in dirs_to_remove:
        try:
            # Only remove if empty
            if d.exists() and not any(d.iterdir()):
                d.rmdir()
        except Exception as e:
            logger.warning(f"Could not remove dir {d}: {e}")
