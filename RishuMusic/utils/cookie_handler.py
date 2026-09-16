import os
import glob
import random
import logging

logger = logging.getLogger("RishuMusic.platforms.Youtube")

# ---------------------------------------------------------------------------
# Cookie directory / file setup
# ---------------------------------------------------------------------------
COOKIE_DIR = os.path.join(os.getcwd(), "cookies")
COOKIE_PATH = os.path.join(COOKIE_DIR, "cookies.txt")

os.makedirs(COOKIE_DIR, exist_ok=True)


def _is_valid_cookie_file(path: str) -> bool:
    """
    Basic sanity check for a Netscape-format cookies.txt file.
    Rejects empty files, non-existent files, or files that don't
    look like a real cookie export (helps catch 'expired/garbage'
    files early instead of failing deep inside yt-dlp).
    """
    if not os.path.isfile(path):
        return False

    if os.path.getsize(path) == 0:
        return False

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return False

    # A valid Netscape cookie file either starts with the standard header
    # or contains at least one tab-separated cookie line for youtube.com.
    has_header = content.lstrip().startswith("# Netscape HTTP Cookie File") or \
                 content.lstrip().startswith("# HTTP Cookie File")
    has_youtube_line = any(
        ("youtube.com" in line or ".youtube.com" in line) and line.count("\t") >= 5
        for line in content.splitlines()
        if line and not line.startswith("#")
    )

    return has_header or has_youtube_line


def _all_cookie_files() -> list:
    """
    Returns every candidate cookie file inside COOKIE_DIR, in case you
    keep several accounts' cookies (cookies1.txt, cookies2.txt, ...)
    to rotate between them and reduce bot-check hits.
    """
    candidates = sorted(glob.glob(os.path.join(COOKIE_DIR, "*.txt")))
    return [c for c in candidates if _is_valid_cookie_file(c)]


def _cookiefile_path() -> str | None:
    """
    Returns a path to a usable cookies.txt file for yt-dlp, or None
    if no valid cookie file is available (in which case the caller
    should simply skip passing --cookies, same as before).

    Behaviour:
      1. If multiple valid cookie files exist in COOKIE_DIR, pick one
         at random each call (basic load-balancing / avoids hammering
         a single account into a fresh bot-check).
      2. If only the default cookies.txt exists and is valid, use it.
      3. If nothing valid is found, log a clear warning and return None.
    """
    valid_files = _all_cookie_files()

    if valid_files:
        chosen = random.choice(valid_files)
        logger.debug(f"Using cookie file: {chosen}")
        return chosen

    if os.path.isfile(COOKIE_PATH):
        logger.warning(
            "cookies.txt exists but failed validation "
            "(empty, corrupted, or wrong format). Skipping --cookies."
        )
    else:
        logger.warning(
            "No cookies.txt found in %s — YouTube bot-check may trigger "
            "on age-restricted/region-locked videos. "
            "Export fresh cookies (Netscape format) and place them here.",
            COOKIE_DIR,
        )

    return None


def build_ytdlp_opts(base_opts: dict) -> dict:
    """
    Helper to merge cookie handling into your existing yt-dlp options dict.
    Use this wherever you currently build opts before calling yt-dlp.

    Example:
        opts = build_ytdlp_opts({
            "format": "bestaudio/best",
            "quiet": True,
        })
        with yt_dlp.YoutubeDL(opts) as ydl:
            ...
    """
    opts = dict(base_opts)  # don't mutate caller's dict
    cookie_file = _cookiefile_path()

    if cookie_file:
        opts["cookiefile"] = cookie_file
    else:
        opts.pop("cookiefile", None)

    return opts
