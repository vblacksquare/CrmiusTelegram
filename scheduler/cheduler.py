
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .message import load_private_messages, load_group_messages
from .lead import load_leads
from .task import load_task_notifications, update_tasks

from .user import update_users
from .group import update_groups

from .email import update_email_jobs


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
    func=load_task_notifications,
    trigger=IntervalTrigger(seconds=1)
)

scheduler.add_job(
    id="update_users",
    func=update_users,
    trigger=IntervalTrigger(seconds=5)
)
scheduler.add_job(
    id="update_groups",
    func=update_groups,
    trigger=IntervalTrigger(seconds=5)
)
scheduler.add_job(
    id="update_tasks",
    func=update_tasks,
    trigger=IntervalTrigger(seconds=5)
)
scheduler.add_job(
    id="update_email_jobs",
    func=update_email_jobs,
    trigger=IntervalTrigger(seconds=5),
    kwargs={"scheduler": scheduler}
)
