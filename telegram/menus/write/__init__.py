
from .write import write_router
from .globale import global_router
from .kick import kick_router
from .to_group import to_group_router


write_router.include_routers(
    global_router,
    kick_router,
    to_group_router
)
