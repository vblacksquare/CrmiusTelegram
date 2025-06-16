
from emitter import emitter, EventType

from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.lead import Lead
from dtypes.settings import Settings


db = Db()
crm = CrmDb()


async def load_leads():
    settings: Settings = await db.ex(dmth.GetOne(Settings, id="main"))
    old_lead_id = settings.last_lead_id
    new_lead_id = 0

    leads = await crm.get_leads(from_id=settings.last_lead_id)
    if not len(leads):
        return

    await db.ex(dmth.AddMany(Lead, leads))

    for lead in leads:
        if lead.crm_id > new_lead_id:
            new_lead_id = lead.crm_id

        emitter.emit(EventType.new_lead, lead)

    if new_lead_id > old_lead_id:
        settings.last_lead_id = new_lead_id
        await db.ex(dmth.UpdateOne(Settings, settings, to_update=["last_lead_id"]))
