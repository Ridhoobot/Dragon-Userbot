import asyncio
from datetime import datetime
from gc import get_objects
from time import time
from userbot import bot, ubot
import psutil
import os
from pyrogram.raw.functions import Ping
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from userbot.core.plugins.str import*
from userbot.config import OWNER_ID
from userbot.core.database.bcast import add_served_user
from userbot.core.database.setvar import get_vars
from userbot.core.helpers.uptime import get_time
from userbot.core.helpers.text import MSG
from userbot.core.helpers.inline import Button
from userbot import start_time
from asyncio import sleep




async def send_msg_to_owner(client, message):
    if message.from_user.id == OWNER_ID:
        return
    else:
        buttons = [
            [
                InlineKeyboardButton(
                    "👤 profil", callback_data=f"profil {message.from_user.id}"
                ),
                InlineKeyboardButton(
                    "jawab 💬", callback_data=f"jawab_pesan {message.from_user.id}"
                ),
            ],
        ]
        await client.send_message(
            OWNER_ID,
            f"<a href=tg://user?id={message.from_user.id}>{message.from_user.first_name} {message.from_user.last_name or ''}</a>\n\n<code>{message.text}</code>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

from pyrogram.errors.exceptions.bad_request_400 import ReactionInvalid

async def ping_cmd(client, message):
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    p = await message.reply("🥶")
    await sleep(1)
    uptime = await get_time((time() - start_time))
    delta_ping = (end - start).microseconds / 1000
    emot_1 = await get_vars(client.me.id, "EMOJI_PING")
    emot_2 = await get_vars(client.me.id, "EMOJI_UPTIME")
    emot_3 = await get_vars(client.me.id, "EMOJI_MENTION")
    emot_pong = emot_1 if emot_1 else "5219943216781995020"
    emot_uptime = emot_2 if emot_2 else "6183961455436498818"
    emot_mention = emot_3 if emot_3 else "5289940334619406906"
    if client.me.is_premium:
        _ping = f"""
<b><emoji id={emot_pong}>🏓</emoji>Pong: <code>{str(delta_ping).replace('.', ',')} ms</code>
<emoji id={emot_uptime}>🕒</emoji>Uptime: <code>{str(uptime).replace('.', ',')} ms</code>
<emoji id={emot_mention}>👑</emoji>Owner: <a href=tg://user?id={client.me.id}>{client.me.first_name} {client.me.last_name or ''}<a><b>
"""
    else:
        _ping = f"""
<b>—ᴘᴏɴɢ: </b> <code>{int(delta_ping)} ms</code>
<b>—ᴜᴘᴛɪᴍᴇ: </b> <code>{uptime}</code>
<b>—ᴏᴡɴᴇʀ: </b> <a href=tg://user?id={client.me.id}>{client.me.first_name} {client.me.last_name or ''}</a>
"""
    await p.edit(_ping)


async def start_cmd(client, message):
    await add_served_user(message.from_user.id)
    await send_msg_to_owner(client, message)
    if len(message.command) < 2:
        buttons = Button.start(message)
        msg = MSG.START(message)
        await message.reply(msg, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        txt = message.text.split(None, 1)[1]
        msg_id = txt.split("_", 1)[1]
        send = await message.reply("<b>tunggu sebentar...</b>")
        if "secretMsg" in txt:
            try:
                m = [obj for obj in get_objects() if id(obj) == int(msg_id)][0]
            except Exception as error:
                return await send.edit(f"<b>❌ error:</b> <code>{error}</code>")
            user_or_me = [m.reply_to_message.from_user.id, m.from_user.id]
            if message.from_user.id not in user_or_me:
                return await send.edit(
                    f"<b>❌ pesan ini bukan untukmu <a href=tg://user?id={message.from_user.id}>{message.from_user.first_name} {message.from_user.last_name or ''}</a>"
                )
            else:
                text = await client.send_message(
                    message.chat.id,
                    m.text.split(None, 1)[1],
                    protect_content=True,
                    reply_to_message_id=message.id,
                )
                await send.delete()
                await asyncio.sleep(120)
                await message.delete()
                await text.delete()
        elif "copyMsg" in txt:
            try:
                m = [obj for obj in get_objects() if id(obj) == int(msg_id)][0]
            except Exception as error:
                return await send.edit(f"<b>❌ error:</b> <code>{error}</code>")
            id_copy = int(m.text.split()[1].split("/")[-1])
            if "t.me/c/" in m.text.split()[1]:
                chat = int("-100" + str(m.text.split()[1].split("/")[-2]))
            else:
                chat = str(m.text.split()[1].split("/")[-2])
            try:
                get = await client.get_messages(chat, id_copy)
                await get.copy(message.chat.id, reply_to_message_id=message.id)
                await send.delete()
            except Exception as error:
                await send.edit(error)

async def stats_ubot(client, message):
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    delta_ping = (end - start).microseconds / 1000
    delta_ping_formatted = round(delta_ping, 3)
    uptime = await get_time((time() - start_time))
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    process = psutil.Process(os.getpid())
    buttons = [[InlineKeyboardButton("Refresh", callback_data="miko")]]
    _ping = f"""
<b>🖥️ [SYSTEM UBOT]
PING: {str(delta_ping_formatted).replace('.', ',')} ms
UBOT: {len(ubot._ubot)} user
UPTIME: {uptime}
OWNER:<b/> @LullaProject

<b>📊 [STATUS SERVER]
CPU: {cpu}%
RAM: {mem}%
DISK: {disk}%
MEMORY: {round(process.memory_info()[0] / 1024 ** 2)} MB</b>
"""
    await message.reply(_ping, reply_markup=InlineKeyboardMarkup(buttons))


async def cb_stats(client, callback_query):
    await callback_query.answer("ʀᴇғʀᴇsʜɪɴɢ...")
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    delta_ping = (end - start).microseconds / 1000
    delta_ping_formatted = round(delta_ping, 3)
    uptime = await get_time((time() - start_time))
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    process = psutil.Process(os.getpid())
    _ping = f"""
<b>🖥️ [SYSTEM UBOT]
PING: {str(delta_ping_formatted).replace('.', ',')} ms
UBOT: {len(ubot._ubot)} user
UPTIME: {uptime}
OWNER:</b> @LullaProject

<b>📊 [STATUS SERVER]
CPU: {cpu}%
RAM: {mem}%
DISK: {disk}%
MEMORY: {round(process.memory_info()[0] / 1024 ** 2)} MB</b>
"""
    buttons = [[InlineKeyboardButton("Refresh", callback_data="miko")]]
    try:
        await callback_query.message.edit(_ping, reply_markup=InlineKeyboardMarkup(buttons))
    except:
        return