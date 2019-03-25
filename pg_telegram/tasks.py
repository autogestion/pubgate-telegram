
from sanic.log import logger
from telethon import TelegramClient, events

from pubgate.db import User
from pubgate.activity import Create
from pubgate.contrib.parsers import process_tags


async def run_tg_bot(app):
    client = TelegramClient('pg_bot_session',
                            app.config.TELEGRAM_API_ID,
                            app.config.TELEGRAM_API_HASH
                            )

    active_bots = await User.find(filter={"details.tgbot.enable": True})
    for bot in active_bots.objects:
        @client.on(events.NewMessage(chats=tuple(bot["details"]["tgbot"]["channels"])))
        async def normal_handler(event):
            content = event.message.text

            # process tags
            extra_tag_list = []
            # collect hardcoded tags from config
            if bot["details"]["tgbot"]["tags"]:
                extra_tag_list.extend(bot["details"]["tgbot"]["tags"])

            content, footer_tags, object_tags = process_tags(extra_tag_list, content)
            body = f"{content}{footer_tags}"

            published = event.message.date.replace(microsecond=0).isoformat() + "Z"

            activity = Create(bot, {
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
            logger.info(f"telegram entry '{event.message.id}' of {bot.name} federating")

    await client.start(bot_token=app.config.TELEGRAM_BOT_TOKEN)

