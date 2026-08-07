from fastapi import APIRouter
from .sip import router as sip_router
from .kb import router as kb_router
from .dispatch import router as dispatch_router
from .sync import router as sync_router

mantra_bridge_router = APIRouter(prefix="/mantra_bridge")

mantra_bridge_router.include_router(sip_router)
mantra_bridge_router.include_router(kb_router)
mantra_bridge_router.include_router(dispatch_router)
mantra_bridge_router.include_router(sync_router)
