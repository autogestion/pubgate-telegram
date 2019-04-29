import asyncio
from collections import defaultdict

from sanic.log import logger
from telethon import TelegramClient, events, utils

from pubgate import MEDIA
from pubgate.db import User, Outbox, Inbox
from pubgate.activity import Create
from pubgate.contrib.parsers import process_tags


async def run_tg_bot(app):
    client = TelegramClient('pg_bot_session',
                            app.config.TELEGRAM_API_ID,
                            app.config.TELEGRAM_API_HASH
                            )
    bot_mapping = defaultdict(set)
    active_bots = await User.find(filter={"details.tgbot.enable": True})
    for bot in active_bots.objects:
        for b_channel in bot["details"]["tgbot"]["channels"]:
            bot_mapping[b_channel].add(bot)

    @client.on(events.NewMessage(chats=tuple(bot_mapping.keys())))
    async def normal_handler(event):
        content = event.message.text
        published = event.message.date.replace(microsecond=0).isoformat() + "Z"

        attachment = []
        if event.message.photo:
            photo_id = f'{bot.name}/{event.message.photo.id}.jpg'
            photo_path = f'{MEDIA}/{photo_id}'
            photo_url = f'{app.base_url}/media/{photo_id}'
            await client.download_media(event.message, photo_path)
            attachment = [{
                "type": "Document",
                "mediaType": "image/jpeg",
                "url": photo_url,
                "name": "null"
            }]

        for triggered_bot in bot_mapping[event.chat.username]:
            # process tags
            extra_tag_list = []
            # collect hardcoded tags from config
            if triggered_bot["details"]["tgbot"]["tags"]:
                extra_tag_list.extend(triggered_bot["details"]["tgbot"]["tags"])

            content, footer_tags, object_tags = process_tags(extra_tag_list, content)
            body = f"{content}{footer_tags}"

            activity = Create(triggered_bot, {
                "type": "Create",
                "cc": [],
                "published": published,
                "object": {
                    "type": "Note",
                    "summary": None,
                    "sensitive": False,
                    "content": body,
                    "published": published,
                    "attachment": attachment,
                    "tag": object_tags
                }
            })
            await activity.save(tg_sent=True)
            await activity.deliver()
            logger.info(f"telegram entry '{event.message.id}' of {triggered_bot.name} federating")

    await client.start(bot_token=app.config.TELEGRAM_BOT_TOKEN)

    while True:
        for bot in active_bots.objects:
            inbox_messages = await Inbox.find(filter={
                "deleted": False,
                "users": {"$in": [bot.name]},
                "activity.type": "Create",
                "tg_sent": {'$ne': True}
            })
            await tg_send(client, bot, inbox_messages.objects, Inbox)

            outbox_messages = await Outbox.find(filter={
                "deleted": False,
                "user_id": bot.name,
                "activity.type": "Create",
                "tg_sent": {'$ne': True}
            })
            await tg_send(client, bot, outbox_messages.objects, Outbox)

        await asyncio.sleep(app.config.CHECK_BOXES_TIMEOUT)


async def tg_send(client, bot, entries, box):
    for entry in entries:
        attachments = entry.activity['object'].get('attachment', [])
        entities = [attachment['url'] for attachment in attachments]
        content = entry.activity['object']['content']
        if content:
            entities.append(content)
        for b_channel in bot["details"]["tgbot"]["channels"]:
            for entity in entities:
                await client.send_message(b_channel, entity)
            await box.update_one(
                {'_id': entry._id},
                {'$set': {"tg_sent": True}}
            )

