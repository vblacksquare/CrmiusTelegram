
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db import Db
from dtypes.db import method as dmth
from dtypes.email import Email


db = Db()
added_email_ids = {}


async def email_job(email: Email):
    print(email)


async def update_email_jobs(scheduler: AsyncIOScheduler):
    emails: list[Email] = await db.ex(dmth.GetMany(Email))
    new_email_ids = list(map(lambda x: x.id, emails))

    for email in emails:
        if email.id in added_email_ids:
            continue

        added_email_ids.update({email.id: email})
        scheduler.add_job(
            id=email.id,
            func=email_job,
            trigger=IntervalTrigger(seconds=1),
            kwargs={'email': email}
        )

    for email_id in list(added_email_ids):
        if email_id in new_email_ids:
            continue

        del added_email_ids[email_id]
        scheduler.remove_job(email_id)
