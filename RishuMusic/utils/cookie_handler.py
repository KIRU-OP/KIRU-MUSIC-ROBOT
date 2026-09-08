import os
import logging

_logger = logging.getLogger("RishuMusic.utils.cookie_handler")

# Path to the cookies.txt file used by yt-dlp for authenticated/age-restricted
# or region-locked YouTube downloads.
#
# If this file does not exist (or is empty), Youtube.py's _cookiefile_path()
# and yt_dlp_download.py's _cookie_opts() will simply skip passing --cookies
# to yt-dlp, so this is safe even if you don't have a cookies.txt file yet.

COOKIE_DIR = os.path.join(os.getcwd(), "cookies")
COOKIE_PATH = os.path.join(COOKIE_DIR, "cookies.txt")

# BUG FIX: this used to be a bare `os.makedirs(COOKIE_DIR, exist_ok=True)`
# at module level with no error handling. Since Youtube.py and
# yt_dlp_download.py both do `from RishuMusic.utils.cookie_handler import
# COOKIE_PATH` at import time, ANY failure here (read-only filesystem,
# permission denied, disk full, etc.) would raise an unhandled OSError and
# crash the entire bot on startup — just because of a cookies folder, even
# though the whole rest of the codebase treats "no cookies" as a totally
# normal, non-fatal case. Now it degrades gracefully instead: logs a warning
# and continues with COOKIE_PATH pointing at a directory that doesn't exist,
# which every existing _cookiefile_path()/_cookie_opts() check already
# handles correctly (they just skip cookies).
try:
    os.makedirs(COOKIE_DIR, exist_ok=True)
except OSError as e:
    _logger.warning(
        "Could not create cookie directory %s (%s) — continuing without "
        "cookie support. Downloads will work but may hit "
        "'Sign in to confirm you're not a bot' more often.",
        COOKIE_DIR, e,
    )
