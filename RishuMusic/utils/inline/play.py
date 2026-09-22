import math
import sys
import platform
from time import time
from datetime import datetime

import pyrogram
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton

from RishuMusic import app
from RishuMusic.utils.formatters import time_to_seconds

# NOTE: adjust this import path to match where `Anony = Call()` actually
# lives in your project (it was defined at the bottom of call.py).
from RishuMusic.core.call import Anony
from RishuMusic.utils.exceptions import AssistantErr


# ============================================================
# Inline keyboard / markup builders
# ============================================================

def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]
    return buttons


def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100
    umm = math.floor(percentage)
    if 0 < umm <= 10:
        bar = "◉—————————"
    elif 10 < umm < 20:
        bar = "—◉————————"
    elif 20 <= umm < 30:
        bar = "——◉———————"
    elif 30 <= umm < 40:
        bar = "———◉——————"
    elif 40 <= umm < 50:
        bar = "————◉—————"
    elif 50 <= umm < 60:
        bar = "—————◉————"
    elif 60 <= umm < 70:
        bar = "——————◉———"
    elif 70 <= umm < 80:
        bar = "———————◉——"
    elif 80 <= umm < 95:
        bar = "————————◉—"
    else:
        bar = "—————————◉"
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="ʏᴛ-ᴀᴘɪ", callback_data=f"oapi"),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="5-", callback_data=f"ADMIN SeekBack|{chat_id}"),
            InlineKeyboardButton(text="5+", callback_data=f"ADMIN SeekForward|{chat_id}"),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close")],
    ]
    return buttons


def stream_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="ʏᴛ-ᴀᴘɪ", callback_data=f"oapi"),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="5-", callback_data=f"ADMIN SeekBack|{chat_id}"),
            InlineKeyboardButton(text="5+", callback_data=f"ADMIN SeekForward|{chat_id}"),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close")],
    ]
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"AnonyPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"AnonyPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="▷",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
    return buttons


# ============================================================
# Callback query handlers
# ============================================================

pver = pyrogram.__version__
BOT_START_TIME = datetime.now()


def get_uptime():
    uptime = datetime.now() - BOT_START_TIME
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"


@app.on_callback_query(filters.regex("oapi"))
async def show_bot_info(c: app, q: CallbackQuery):
    start = time()
    m = await c.send_message(q.message.chat.id, "🧾ᴀᴘɪ sᴛᴀᴛᴜs........")
    delta_ping = (time() - start) * 1000
    await m.delete()

    short_txt = f"""
🧾ᴀᴘɪ sᴛᴀᴛᴜs

ᴅʙ : ᴏɴʟɪɴᴇ
ʀɪsʜᴜ ᴀᴘɪ : ʀᴇsᴘᴏɴsɪᴠᴇ
ᴀᴘɪ ᴘɪɴɢ : {delta_ping:.2f} ms
ᴀᴘɪ ᴜᴘᴛɪᴍᴇ : {get_uptime()}

✅ ᴇᴠᴇʀʏᴛʜɪɴɢ ғɪɴᴇ
"""
    await q.answer(short_txt.strip(), show_alert=True)


@app.on_callback_query(filters.regex(r"^ADMIN SeekBack\|"))
async def seek_back_5s(c: app, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])
    try:
        await Anony.seek_backward_stream(chat_id, 5)
        await q.answer("⏪ Rewound 5 seconds.")
    except AssistantErr as e:
        await q.answer(str(e), show_alert=True)
    except Exception:
        await q.answer("Couldn't rewind — nothing playing or seek failed.", show_alert=True)


@app.on_callback_query(filters.regex(r"^ADMIN SeekForward\|"))
async def seek_forward_5s(c: app, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])
    try:
        await Anony.seek_forward_stream(chat_id, 5)
        await q.answer("⏩ Skipped ahead 5 seconds.")
    except AssistantErr as e:
        await q.answer(str(e), show_alert=True)
    except Exception:
        await q.answer("Couldn't skip ahead — nothing playing or seek failed.", show_alert=True)
