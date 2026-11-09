from fastapi import APIRouter

from app.api.v1.events import router as events_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.teacher import router as teacher_router

api_router = APIRouter()
api_router.include_router(sessions_router)
api_router.include_router(events_router)
api_router.include_router(teacher_router)
