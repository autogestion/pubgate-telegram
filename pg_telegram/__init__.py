__version__ = "0.1.7"

from pg_telegram.tasks import run_tg_bot

pg_blueprints = []
pg_tasks = [run_tg_bot]
