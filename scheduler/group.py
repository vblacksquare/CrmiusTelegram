
from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.group import Group


db = Db()
crm = CrmDb()


async def update_groups():
    new_groups = await crm.get_groups()

    old_groups: list[Group] = await db.ex(dmth.GetMany(Group))
    old_groups_ids: list[str] = list(map(lambda x: x.id, old_groups))

    to_add = []

    for new_group in new_groups:
        if new_group.id in old_groups_ids:
            await db.ex(dmth.UpdateOne(Group, new_group))

        else:
            to_add.append(new_group)

    if len(to_add):
        await db.ex(dmth.AddMany(Group, to_add))
