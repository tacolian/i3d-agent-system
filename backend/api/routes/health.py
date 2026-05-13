"""
健康检查API路由
"""
from typing import Dict
from fastapi import APIRouter, Depends
from datetime import datetime

from ...models.schema import HealthCheck
from ...config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthCheck)
async def health_check():
    """
    健康检查接口

    返回服务状态和依赖服务健康情况
    """
    services = {}

    # 检查数据库连接
    try:
        from ...db.session import async_engine
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
        services["database"] = "healthy"
    except Exception:
        services["database"] = "unhealthy"

    # 检查Redis连接
    try:
        from ...services.cache_service import get_cache_service
        cache = get_cache_service()
        await cache.ping()
        services["redis"] = "healthy"
    except Exception:
        services["redis"] = "unhealthy"

    # 检查RabbitMQ连接
    try:
        from ...services.mq_service import get_mq_service
        mq = get_mq_service()
        await mq.ping()
        services["rabbitmq"] = "healthy"
    except Exception:
        services["rabbitmq"] = "unhealthy"

    # 确定整体状态
    if all(status == "healthy" for status in services.values()):
        status = "healthy"
    elif any(status == "healthy" for status in services.values()):
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthCheck(
        status=status,
        version=settings.APP_VERSION,
        timestamp=datetime.now(),
        services=services,
    )


@router.get("/ping")
async def ping():
    """
    简单的ping接口
    """
    return {"ping": "pong", "timestamp": datetime.now().isoformat()}


@router.get("/ready")
async def readiness():
    """
    就绪检查接口

    用于Kubernetes readiness probe
    """
    # 检查关键依赖是否就绪
    try:
        from ...db.session import async_engine
        from ...services.cache_service import get_cache_service

        # 数据库连接检查
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")

        # Redis连接检查
        cache = get_cache_service()
        await cache.ping()

        return {"ready": True}
    except Exception:
        return {"ready": False}
