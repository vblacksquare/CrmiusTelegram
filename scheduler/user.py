
from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser


db = Db()
crm = CrmDb()


async def update_users():
    new_users = await crm.get_users()

    if new_users is None:
        return

    new_users_ids = list(map(lambda x: x.id, new_users))

    old_users: list[CrmUser] = await db.ex(dmth.GetMany(CrmUser))
    old_users_ids: list[str] = list(map(lambda x: x.id, old_users))

    to_add = []

    for new_user in new_users:
        if new_user.id in old_users_ids:
            await db.ex(dmth.UpdateOne(CrmUser, new_user, to_update=["id", "login", "password", "first_name", "last_name", "image", "chat_id"]))

        else:
            to_add.append(new_user)

    if len(to_add):
        await db.ex(dmth.AddMany(CrmUser, to_add))

    for old_user in old_users:
        if old_user.id in new_users_ids:
            continue

        await db.ex(dmth.RemoveOne(CrmUser, old_user))

        if not old_user.user_id:
            continue

        tuser: User = await db.ex(dmth.GetOne(User, id=old_user.user_id))

        if not tuser:
            continue

        tuser.crm_id = None
        tuser.is_verified = False
        await db.ex(dmth.UpdateOne(User, tuser, to_update=["crm_id", "is_verified"]))
