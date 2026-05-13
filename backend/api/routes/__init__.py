"""
API路由模块
"""
from .chat import router as chat_router
from .health import router as health_router
from .upload import router as upload_router

__all__ = ["chat_router", "health_router", "upload_router"]
