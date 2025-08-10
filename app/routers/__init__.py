from .auth import router as auth_router
from .oauth2 import router as oauth2_router
from .user import router as user_router

__all__ = ["auth_router", "oauth2_router", "user_router"]
