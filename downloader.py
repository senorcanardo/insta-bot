import os
import logging
import tempfile
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

COOKIES_FILE = os.environ.get("COOKIES_FILE", "cookies.txt")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB Telegram limit


def is_video_url(url: str) -> bool:
    return "/reel/" in url or "/tv/" in url


def download_with_ytdlp(url: str, output_dir: str) -> list[Path]:
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-o", f"{output_dir}/%(title)s_%(id)s.%(ext)s",
        "--merge-output-format", "mp4",
        "--no-check-formats",
        url
    ]
    if os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])
        logger.info("yt-dlp: using cookies.")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    logger.info(f"yt-dlp stdout: {result.stdout[-300:]}")

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr[-300:]}")

    return collect_files(output_dir)


def download_with_gallerydl(url: str, output_dir: str) -> list[Path]:
    cmd = [
        "gallery-dl",
        "--dest", output_dir,
        "--filename", "{filename}.{extension}",
        url
    ]
    if os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])
        logger.info("gallery-dl: using cookies.")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    logger.info(f"gallery-dl stdout: {result.stdout[-300:]}")

    if result.returncode != 0:
        raise RuntimeError(f"gallery-dl failed: {result.stderr[-300:]}")

    return collect_files(output_dir)


def collect_files(output_dir: str) -> list[Path]:
    media_extensions = {".mp4", ".mov", ".webm", ".jpg", ".jpeg", ".png", ".webp"}
    files = sorted([
        Path(output_dir) / f
        for f in os.listdir(output_dir)
        if Path(f).suffix.lower() in media_extensions
    ])

    oversized = [f for f in files if f.stat().st_size > MAX_FILE_SIZE]
    if oversized:
        logger.warning(f"{len(oversized)} file(s) exceed 50MB and will be skipped.")
    files = [f for f in files if f.stat().st_size <= MAX_FILE_SIZE]

    return files


def download_instagram_media(url: str) -> list[Path]:
    tmp_dir = tempfile.mkdtemp(prefix="instabot_")
    logger.info(f"Downloading {url} to {tmp_dir}")

    try:
        if is_video_url(url):
            logger.info("Detected video/reel — using yt-dlp")
            files = download_with_ytdlp(url, tmp_dir)
        else:
            logger.info("Detected photo post — using gallery-dl")
            files = download_with_gallerydl(url, tmp_dir)

        if not files:
            raise RuntimeError("No media files were downloaded.")

        logger.info(f"Successfully downloaded {len(files)} file(s).")
        return files

    except Exception:
        cleanup(collect_files(tmp_dir))
        raise


def cleanup(files: list[Path]):
    dirs = set()
    for f in files:
        dirs.add(f.parent)
        try:
            f.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Could not delete {f}: {e}")
    for d in dirs:
        try:
            if d.exists() and not any(d.iterdir()):
                d.rmdir()
        except Exception as e:
            logger.warning(f"Could not remove dir {d}: {e}")
