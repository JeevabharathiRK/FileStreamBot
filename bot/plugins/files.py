from hydrogram import filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from secrets import token_hex
import re
from bot import TelegramBot
from bot.config import Telegram, Server
from bot.modules.decorators import verify_user
from bot.modules.static import *

# This handler listens to messages in group chats and handles file uploads
@TelegramBot.on_message(filters.command('link') & filters.group)
@verify_user
async def handle_user_file(_, msg: Message):
    if msg.reply_to_message:
        replied_message = msg.reply_to_message
        # Check for supported file types in the replied message
        if any([
            replied_message.document,
            replied_message.video,
            replied_message.video_note,
            replied_message.audio,
            replied_message.voice,
            replied_message.photo
        ]):
            sender_id = msg.from_user.id
            secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
            
            # Copy the file to the specified channel
            file = await replied_message.copy(
                chat_id=Telegram.CHANNEL_ID,
                caption=f'||{secret_code}/{sender_id}||'
            )
            
            file_id = file.id  # Get the file ID from the copied file
            dl_link = f'{Server.BASE_URL}/dl/{file_id}?code={secret_code}'

            # Generate stream link for videos
            if (replied_message.document and 'video' in replied_message.document.mime_type) or replied_message.video:
                stream_link = f'{Server.BASE_URL}/stream/{file_id}?code={secret_code}'
                await msg.reply(
                    text=MediaLinksText % {'dl_link': dl_link, 'stream_link': stream_link},
                    quote=True,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('Download', url=dl_link),
                                InlineKeyboardButton('Stream', url=stream_link)
                            ],
                            [
                                InlineKeyboardButton('Revoke', callback_data=f'rm_{file_id}_{secret_code}')
                            ]
                        ]
                    )
                )
            else:
                # Respond with only a download link for non-video files
                await msg.reply(
                    text=FileLinksText % {'dl_link': dl_link},
                    quote=True,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('Download', url=dl_link),
                                InlineKeyboardButton('Revoke', callback_data=f'rm_{file_id}_{secret_code}')
                            ]
                        ]
                    )
                )
        else:
            # Handle invalid file types
            await msg.reply(
                text="Sorry, it looks like the file type isn’t supported. Try sending it again and reply to it using /link.",
                quote=False
            )
    else:
        # Handle missing reply
        await msg.reply(
            text="Please reply to a file message with the `/link` command to get the download or stream link.",
            quote=False
        )

# Trigger on files posted in the storage channel whose caption contains "Start"
@TelegramBot.on_message(
    filters.chat(Telegram.CHANNEL_ID)
    & (
        filters.document
        | filters.video
        | filters.video_note
        | filters.audio
        | filters.voice
        | filters.photo
    )
)
async def handle_storage_channel_file(client, msg: Message):
    caption = msg.caption or ""
    if "Start" not in caption:
        return

    # If a secret is already present in caption, reuse it; else create one and copy
    code_match = re.search(r"\|\|([0-9a-fA-F]+)\/(\d+)\|\|", caption)
    if code_match:
        secret_code = code_match.group(1)
        sender_id = int(code_match.group(2))
        file_id = msg.id
    else:
        secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
        # Best effort sender id; channels often lack from_user
        sender_id = msg.from_user.id if msg.from_user else 0

        # Copy so the bot owns the message in channel and can store the code in caption
        copied = await msg.copy(
            chat_id=Telegram.CHANNEL_ID,
            caption=f"||{secret_code}/{sender_id}||"
        )
        file_id = copied.id

    dl_link = f"{Server.BASE_URL}/dl/{file_id}?code={secret_code}"

    is_video = bool(
        (msg.document and msg.document.mime_type and "video" in msg.document.mime_type)
        or msg.video
        or msg.video_note
    )

    if is_video:
        stream_link = f"{Server.BASE_URL}/stream/{file_id}?code={secret_code}"
        text = MediaLinksText % {"dl_link": dl_link, "stream_link": stream_link}
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Download", url=dl_link),
                    InlineKeyboardButton("Stream", url=stream_link),
                ],
                [InlineKeyboardButton("Revoke", callback_data=f"rm_{file_id}_{secret_code}")],
            ]
        )
    else:
        text = FileLinksText % {"dl_link": dl_link}
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Download", url=dl_link),
                    InlineKeyboardButton("Revoke", callback_data=f"rm_{file_id}_{secret_code}"),
                ]
            ]
        )

    # Send the same message as /link to the target group
    if Telegram.LINKS_GROUP_ID:
        await client.send_message(
            chat_id=Telegram.LINKS_GROUP_ID,
            text=text,
            reply_markup=keyboard,
        )
