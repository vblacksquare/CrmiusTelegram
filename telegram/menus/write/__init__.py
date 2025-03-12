
from .write import write_router
from .globale import global_router
from .kick import kick_router
from .plan import plan_router


write_router.include_routers(
    global_router,
    kick_router,
    plan_router
)
