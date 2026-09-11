import asyncio

# Tuning / performance constants used across VIPMUSIC.platforms.Youtube

YTDLP_TIMEOUT = 60
YOUTUBE_META_MAX = 200
YOUTUBE_META_TTL = 300

CHUNK_SIZE = 1024 * 64          # 64KB per chunk when streaming API downloads
SEM = asyncio.Semaphore(4)      # max 4 concurrent downloads at once
