
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .messages import load_private_messages, load_group_messages
from .lead import load_leads
from .task import load_tasks


scheduler = AsyncIOScheduler()
scheduler.add_job(
    id="load_private_messages",
    func=load_private_messages,
    trigger=IntervalTrigger(seconds=1)
)
scheduler.add_job(
    id="load_group_messages",
    func=load_group_messages,
    trigger=IntervalTrigger(seconds=1)
)
scheduler.add_job(
    id="load_leads",
    func=load_leads,
    trigger=IntervalTrigger(seconds=1)
)
scheduler.add_job(
    id="load_tasks",
    func=load_tasks,
    trigger=IntervalTrigger(seconds=1)
)

