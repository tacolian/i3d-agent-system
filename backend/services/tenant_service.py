"""
租户服务
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..config import settings, TenantConfig


class TenantService:
    """
    租户服务

    功能:
    1. 租户信息管理
    2. 租户配置获取
    3. 租户隔离验证
    """

    # 租户配置（可以从数据库加载）
    TENANT_CONFIGS = {
        "shenfa": {
            "name": "申发",
            "bucket": "shenfa-files",
            "enabled": True,
        },
        "meidi": {
            "name": "美的",
            "bucket": "meidi-files",
            "enabled": True,
        },
        "dongjiang": {
            "name": "东江",
            "bucket": "dongjiang-files",
            "enabled": True,
        },
        "huabei": {
            "name": "华北",
            "bucket": "huabei-files",
            "enabled": True,
        },
    }

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        获取租户信息

        Args:
            tenant_id: 租户ID

        Returns:
            租户信息，如果不存在返回None
        """
        return self.TENANT_CONFIGS.get(tenant_id)

    def is_valid_tenant(self, tenant_id: str) -> bool:
        """验证租户ID是否有效"""
        return tenant_id in self.TENANT_CONFIGS

    def is_tenant_enabled(self, tenant_id: str) -> bool:
        """检查租户是否启用"""
        info = self.get_tenant_info(tenant_id)
        return info is not None and info.get("enabled", False)

    def get_tenant_bucket(self, tenant_id: str) -> Optional[str]:
        """获取租户的MinIO桶名"""
        info = self.get_tenant_info(tenant_id)
        return info.get("bucket") if info else None

    def get_tenant_vector_table(self, tenant_id: str) -> str:
        """获取租户的向量表名"""
        return f"tenant_{tenant_id}_vectors"

    def get_all_tenants(self) -> List[str]:
        """获取所有租户ID列表"""
        return list(self.TENANT_CONFIGS.keys())

    def get_enabled_tenants(self) -> List[str]:
        """获取所有启用的租户ID列表"""
        return [
            tid for tid, config in self.TENANT_CONFIGS.items()
            if config.get("enabled", False)
        ]


# ============================================================================
# 全局实例
# ============================================================================

_tenant_service: Optional[TenantService] = None


def get_tenant_service() -> TenantService:
    """获取租户服务单例"""
    global _tenant_service
    if _tenant_service is None:
        _tenant_service = TenantService()
    return _tenant_service
