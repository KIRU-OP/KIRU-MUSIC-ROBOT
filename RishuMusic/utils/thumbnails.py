import os
import re

import aiofiles
import aiohttp
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch

from RishuMusic import app
from config import YOUTUBE_IMG_URL


def changeImageSize(maxWidth, maxHeight, image):
    """Resize with high-quality Lanczos resampling instead of the default
    (nearest-neighbor), which is what made the original output look soft/blocky."""
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight), Image.LANCZOS)
    return newImage


def circle(img, scale=4):
    """Anti-aliased circular crop.

    The original drew the pieslice mask at the target size, giving a
    hard, jagged (staircase) edge. Here we draw the mask at `scale`x
    resolution and downsample it with Lanczos, which produces a smooth,
    anti-aliased circular edge (the same trick used for supersampled AA).
    """
    img = img.convert("RGBA")
    w, h = img.size

    big_w, big_h = w * scale, h * scale
    mask_big = Image.new("L", (big_w, big_h), 0)
    draw = ImageDraw.Draw(mask_big)
    draw.ellipse((0, 0, big_w, big_h), fill=255)
    mask = mask_big.resize((w, h), Image.LANCZOS)

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def clear(text):
    words = text.split(" ")
    title = ""
    for w in words:
        if len(title) + len(w) < 60:
            title += " " + w
    return title.strip()


def _best_thumbnail_url(thumbnails):
    """Original code always took thumbnails[0], which is often the
    smallest/lowest-quality entry the API returns. Pick the largest
    available image instead (fallback to a maxresdefault guess)."""
    if not thumbnails:
        return None
    best = max(
        thumbnails,
        key=lambda t: (t.get("width", 0) or 0) * (t.get("height", 0) or 0),
    )
    return best["url"].split("?")[0]


async def get_thumb(videoid, user_id):
    cache_path = f"cache/{videoid}_{user_id}.png"
    if os.path.isfile(cache_path):
        return cache_path

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        search_result = (await results.next())["result"]
        for result in search_result:
            try:
                title = result["title"]
                title = re.sub(r"\W+", " ", title)
                title = title.title()
            except Exception:
                title = "Unsupported Title"
            try:
                duration = result["duration"]
            except Exception:
                duration = "Unknown Mins"

            thumbnail = _best_thumbnail_url(result.get("thumbnails", []))
            if not thumbnail:
                # last-ditch fallback: YouTube's guaranteed maxres/high-res path
                thumbnail = f"https://i.ytimg.com/vi/{videoid}/maxresdefault.jpg"

            try:
                views = result["viewCount"]["short"]
            except Exception:
                views = "Unknown Views"
            try:
                channel = result["channel"]["name"]
            except Exception:
                channel = "Unknown Channel"

        os.makedirs("cache", exist_ok=True)

        thumb_raw_path = f"cache/thumb{videoid}.png"
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_raw_path, mode="wb") as f:
                        await f.write(await resp.read())
                elif thumbnail.endswith("maxresdefault.jpg"):
                    raise RuntimeError("maxres thumbnail unavailable")
                else:
                    # retry once against the guaranteed maxresdefault path
                    fallback_url = f"https://i.ytimg.com/vi/{videoid}/maxresdefault.jpg"
                    async with session.get(fallback_url) as resp2:
                        async with aiofiles.open(thumb_raw_path, mode="wb") as f:
                            await f.write(await resp2.read())

        try:
            async for photo in app.get_chat_photos(user_id, 1):
                sp = await app.download_media(photo.file_id, file_name=f"{user_id}.jpg")
        except Exception:
            async for photo in app.get_chat_photos(app.id, 1):
                sp = await app.download_media(photo.file_id, file_name=f"{app.id}.jpg")

        xp = Image.open(sp)

        youtube = Image.open(thumb_raw_path)
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")

        # Slightly lighter blur + sharpen pass afterwards keeps the
        # background from turning to mush at high res.
        background = image2.filter(ImageFilter.GaussianBlur(8))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.5)

        y = changeImageSize(200, 200, circle(youtube))
        background.paste(y, (45, 225), mask=y)
        a = changeImageSize(200, 200, circle(xp))
        background.paste(a, (1045, 225), mask=a)

        draw = ImageDraw.Draw(background)
        arial = ImageFont.truetype("RishuMusic/assets/font2.ttf", 30)
        font = ImageFont.truetype("RishuMusic/assets/font.ttf", 30)

        draw.text((1110, 8), unidecode(app.name), fill="white", font=arial)
        draw.text((55, 560), f"{channel} | {views[:23]}", (255, 255, 255), font=arial)
        draw.text((57, 600), clear(title), (255, 255, 255), font=font)
        draw.line([(55, 660), (1220, 660)], fill="white", width=5, joint="curve")
        draw.ellipse([(918, 648), (942, 672)], outline="white", fill="white", width=15)
        draw.text((36, 685), "00:00", (255, 255, 255), font=arial)
        draw.text((1185, 685), f"{duration[:23]}", (255, 255, 255), font=arial)

        # Mild sharpen to counteract the softness introduced by blur/resize,
        # then save uncompressed PNG (no lossy re-encode) for a crisp result.
        background = background.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))
        background = background.convert("RGB")

        try:
            os.remove(thumb_raw_path)
        except Exception:
            pass

        background.save(cache_path, format="PNG", optimize=True)
        return cache_path
    except Exception as e:
        # DEBUG: previously this swallowed every error silently, so it
        # always fell back to YOUTUBE_IMG_URL with no way to know why.
        # Print/log the real error so the actual failure point is visible.
        import traceback
        print(f"[get_thumb] Failed to generate custom thumbnail: {e}")
        traceback.print_exc()
        return YOUTUBE_IMG_URL
