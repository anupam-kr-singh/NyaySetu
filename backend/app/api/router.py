"""API router assembly. Product routes live under /api."""

from fastapi import APIRouter

from app.api import auth, dev, lawyers
from app.core.config import get_settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(lawyers.router)

if get_settings().is_development:
    api_router.include_router(dev.router)
