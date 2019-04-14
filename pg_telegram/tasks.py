import asyncio
from collections import defaultdict

from sanic.log import logger
from telethon import TelegramClient, events

from pubgate.db import User, Outbox
from pubgate.db.queries import aggregate_boxes
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
                    "attachment": [],
                    "tag": object_tags
                }
            })
            await activity.save()
            await activity.deliver()
            logger.info(f"telegram entry '{event.message.id}' of {triggered_bot.name} federating")

    await client.start(bot_token=app.config.TELEGRAM_BOT_TOKEN)

    while True:
        for bot in active_bots.objects:
            db_query = aggregate_boxes(
                {"tg_sent": "$tg_sent",
                 "user_id": "$user_id"}
            )
            db_query.append(
                {'$match': {
                    "deleted": False,
                    "$or": [{"user_id": bot.name},
                            {"users": {"$in": [bot.name]}}],
                    "activity.type": "Create",
                    "tg_sent": False
                }},
            )
            new_entries = await Outbox.aggregate(db_query)
            for entry in new_entries:
                for b_channel in bot["details"]["tgbot"]["channels"]:
                    await client.send_message(b_channel, entry.activity.object.content)

                #TODO mark as sent to tg

        await asyncio.sleep(app.config.CHECK_BOXES_TIMEOUT)






