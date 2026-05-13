"""
API依赖项
"""
from typing import Optional
from fastapi import Header, HTTPException, Depends

from ..models.schema import TenantContext
from ..config import settings, TenantConfig


async def get_tenant_context(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> TenantContext:
    """
    从请求头中提取租户上下文

    Args:
        x_tenant_id: 租户ID
        x_user_id: 用户ID（可选）
        x_request_id: 请求ID（可选）

    Returns:
        租户上下文

    Raises:
        HTTPException: 如果租户ID无效
    """
    if not TenantConfig.is_valid_tenant(x_tenant_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tenant_id: {x_tenant_id}",
        )

    return TenantContext(
        tenant_id=x_tenant_id,
        user_id=x_user_id,
        request_id=x_request_id,
    )


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> bool:
    """
    验证API密钥（如果配置了的话）

    Args:
        x_api_key: API密钥

    Returns:
        True

    Raises:
        HTTPException: 如果API密钥无效
    """
    # 如果没有配置API密钥，跳过验证
    if not settings.API_KEY_HEADER:
        return True

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
        )

    # TODO: 实际的API密钥验证逻辑
    # 这里简化处理
    if x_api_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return True
