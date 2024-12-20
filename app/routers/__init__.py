from app.routers.auth import router as auth_router
from app.routers.game import router as game_router
from app.routers.main import router as main_router

__all__ = ['auth_router', 'game_router', 'main_router']
