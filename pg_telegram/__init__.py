__version__ = "0.1.9"

from pg_telegram.tasks import run_tg_bot

pg_blueprints = []
pg_tasks = [run_tg_bot]
