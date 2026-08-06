from fastapi import APIRouter

from app.api.v1.routers import (
    admin_router,
    auth_router,
    category_router,
    destination_router,
    favorite_router,
    health_router,
    history_router,
    map_router,
    rating_router,
    recommendation_router,
    user_router,
    weather_router,
    websocket_router,
)

api_router = APIRouter()
api_router.include_router(health_router.router)
api_router.include_router(auth_router.router)
api_router.include_router(user_router.router)
api_router.include_router(category_router.router)
api_router.include_router(destination_router.router)
api_router.include_router(favorite_router.router)
api_router.include_router(history_router.router)
api_router.include_router(map_router.router)
api_router.include_router(weather_router.router)
api_router.include_router(recommendation_router.router)
api_router.include_router(rating_router.router)
api_router.include_router(admin_router.router)
api_router.include_router(websocket_router.router)
