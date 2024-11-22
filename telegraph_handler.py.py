import json
from typing import TYPE_CHECKING, Any, List, Optional

import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from selfbot import Bot, State
from selfbot.helpers import generate_inline_query, send_inline_bot_result

from .catbox_handler import upload_to_catbox

if TYPE_CHECKING:
    from pyrogram.types import Message, MessageEntity

    from selfbot import App


@Client.on_message(filters.me & filters.command("tg", ""))
async def telegraph_handler(client: "App", message: "Message") -> None:
    reply_message = message.reply_to_message
    if not reply_message:
        return

    text, entities, webpage_or_photo = None, None, None
    if reply_message.text:
        text, entities = reply_message.text, reply_message.entities
        if (
            hasattr(reply_message, "web_page_preview")
            and reply_message.web_page_preview.webpage.photo
        ):
            webpage_or_photo = "webpage"
            url = getattr(reply_message.web_page_preview.webpage, "url", None)
            if url:
                image_node = {"tag": "img", "attrs": {"src": url}}
    elif reply_message.photo and reply_message.caption:
        text, entities, webpage_or_photo = (
            reply_message.caption,
            reply_message.caption_entities,
            "photo",
        )

        await message.edit_text("<b>Downloading...</b>")
        dl_path = await client.download_media(reply_message.photo.file_id)

        await message.edit_text("<b>Uploading...</b>")
        catbox_url = await upload_to_catbox(dl_path=dl_path)

        image_node = {"tag": "img", "attrs": {"src": catbox_url}}
    elif reply_message.caption:
        text, entities = reply_message.caption, reply_message.caption_entities
    else:
        await message.edit_text("<b>Reply to Text!</b>")
        return

    message_text = "<pre language='Message Text'>Pasted to Telegraph!</pre>"
    page_title = f"{str(message.chat.id).replace('-100', '')} {reply_message.id}"
    if len(message.command) > 1:
        page_title = message.text.split(maxsplit=1)[1]
        message_text = f"<pre language='Pasted to Telegraph'>Title: {page_title}</pre>"

    async def create_telegraph_page(
        access_token: str,
        title: str,
        content: List[Any],
        author_name: str,
        author_url: str,
    ) -> Optional[str]:
        async with aiohttp.ClientSession() as client:
            data = {
                "access_token": access_token,
                "title": title,
                "content": json.dumps(content),
            }
            if author_name:
                data["author_name"] = author_name
            if author_url:
                data["author_url"] = author_url

            API_CREATE_PAGE_URL = "https://api.telegra.ph/createPage"
            async with client.post(API_CREATE_PAGE_URL, json=data) as response:
                if response.status == 200:
                    dtext = await response.text()
                    djson = json.loads(dtext)
                    if djson.get("ok") and "result" in djson:
                        return djson["result"]["url"]

        return None

    await message.edit_text("<b>Pasting...</b>")

    nodes = parse_entities_to_nodes(text, entities)
    if webpage_or_photo == "photo":
        nodes.insert(0, image_node)
    elif webpage_or_photo == "webpage":
        nodes.append(image_node)

    telegraph_url = await create_telegraph_page(
        access_token=client.TELEGRAPH_ACCESS_TOKEN,
        title=page_title,
        content=nodes,
        author_name=Bot.me.full_name,
        author_url=f"https://t.me/{Bot.me.username}",
    )

    button_url = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Copy", copy_text=telegraph_url),
                InlineKeyboardButton("Open", url=telegraph_url),
            ]
        ]
    )

    state_key = f"Telegraph | {message.chat.id} | {message.id}"
    state_value = generate_inline_query(text=message_text, reply_markup=button_url)

    State.set_data(state_key, state_value)

    sent_inline = await send_inline_bot_result(
        client, message, query=state_key, reply_to_message_id=reply_message.id
    )
    if sent_inline:
        await message.delete()


def parse_entities_to_nodes(text: str, entities: List["MessageEntity"]) -> List[Any]:
    nodes = []
    last_offset = 0
    current_line = []

    def add_to_current_line(content):
        if (
            isinstance(content, str)
            and current_line
            and isinstance(current_line[-1], str)
        ):
            current_line[-1] += content
        else:
            current_line.append(content)

    def flush_current_line():
        if current_line:
            nodes.append({"tag": "p", "children": current_line.copy()})
            current_line.clear()

    def handle_plain_text(plain_text):
        parts = plain_text.split("\n")
        for i, part in enumerate(parts):
            if part:
                add_to_current_line(part)
            if i < len(parts) - 1:
                flush_current_line()
                nodes.append({"tag": "br"})

    def apply_format(entity_type, content, entity=None):
        if entity_type == MessageEntityType.BOLD:
            return {"tag": "b", "children": [content]}
        elif entity_type == MessageEntityType.ITALIC:
            return {"tag": "i", "children": [content]}
        elif entity_type == MessageEntityType.UNDERLINE:
            return {"tag": "u", "children": [content]}
        elif entity_type == MessageEntityType.STRIKETHROUGH:
            return {"tag": "s", "children": [content]}
        elif entity_type == MessageEntityType.CODE:
            return {"tag": "code", "children": [content]}
        elif entity_type == MessageEntityType.PRE:
            return {"tag": "pre", "children": [content]}
        elif entity_type == MessageEntityType.TEXT_LINK:
            return {"tag": "a", "attrs": {"href": entity.url}, "children": [content]}
        elif entity_type == MessageEntityType.BLOCKQUOTE:
            return {"tag": "blockquote", "children": [content]}
        elif entity_type == MessageEntityType.URL:
            return {"tag": "a", "attrs": {"href": content}, "children": [content]}
        else:
            return content

    if entities is not None:
        entities = sorted(entities, key=lambda e: (e.offset, e.length))
    else:
        entities = []

    for entity in entities:
        if entity.offset > last_offset:
            plain_text = text[last_offset : entity.offset]
            handle_plain_text(plain_text)

        formatted_content = apply_format(
            entity.type, text[entity.offset : entity.offset + entity.length], entity
        )
        add_to_current_line(formatted_content)
        last_offset = entity.offset + entity.length

    if last_offset < len(text):
        plain_text = text[last_offset:]
        handle_plain_text(plain_text)

    flush_current_line()

    return nodes
