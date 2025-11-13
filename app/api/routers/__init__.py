from fastapi import APIRouter

from app.api.routers import team_router, user_router

api_router = APIRouter()
api_router.include_router(team_router.router)
api_router.include_router(user_router.router)
