from fastapi import APIRouter

from app.api.v1.wallets import router as wallets_router

api_router = APIRouter()
api_router.include_router(wallets_router)

__all__ = ["api_router"]