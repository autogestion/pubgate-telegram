import asyncio
from collections import defaultdict

from sanic.log import logger
from telethon import TelegramClient, events
from markdown import markdown

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
        content = markdown(event.message.text)
        published = event.message.date.replace(microsecond=0).isoformat() + "Z"

        attachment = []
        if event.message.photo:
            photo_id = f'{bot.name}/{event.message.photo.id}.jpg'
            await client.download_media(event.message, f'{MEDIA}/{photo_id}')
            attachment = [{
                "type": "Document",
                "mediaType": "image/jpeg",
                "url": f'{app.base_url}/media/{photo_id}',
                "name": "null"
            }]

        for triggered_bot in bot_mapping[event.chat.username]:
            # process tags
            extra_tag_list = []
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
        # url of original entry is sufficient if we do link_preview
        # more on message formatting https://github.com/autogestion/pubgate-telegram/pull/3
        url = entry.activity['object'].get('url') or entry.activity['object'].get('id')
        if url:
            for b_channel in bot["details"]["tgbot"]["channels"]:
                await client.send_message(b_channel, url,
                                          parse_mode='html',
                                          link_preview=True)
        # TODO fix issue when more then 1 bot recieved same object in inbox
        await box.update_one(
            {'_id': entry._id},
            {'$set': {"tg_sent": True}}
        )
