from aiogram import Router

from . import common, onboarding, recommend

def build_router() -> Router:
    root = Router(name="root")
    root.include_routers(
        common.router,
        onboarding.router,
        recommend.router,
        common.fallback_router
    )
    return root