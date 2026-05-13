"""
状态管理器
管理Agent会话状态和持久化
"""
from typing import Dict, Any, Optional
import json
import asyncio

from ..config import settings
from ..services.cache_service import get_cache_service


class StateManager:
    """
    状态管理器

    功能:
    1. 会话状态缓存
    2. 状态持久化
    3. 状态恢复
    4. 状态清理
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.state_ttl = settings.REDIS_SESSION_TTL

    async def save_state(
        self,
        session_id: str,
        tenant_id: str,
        state: Dict[str, Any],
    ) -> None:
        """
        保存会话状态

        Args:
            session_id: 会话ID
            tenant_id: 租户ID
            state: 状态数据
        """
        key = self._make_state_key(session_id, tenant_id)
        await self.cache.set(
            key,
            json.dumps(state),
            expire=self.state_ttl,
        )

    async def load_state(
        self,
        session_id: str,
        tenant_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        加载会话状态

        Args:
            session_id: 会话ID
            tenant_id: 租户ID

        Returns:
            状态数据，如果不存在返回None
        """
        key = self._make_state_key(session_id, tenant_id)
        data = await self.cache.get(key)

        if data:
            return json.loads(data)
        return None

    async def update_state(
        self,
        session_id: str,
        tenant_id: str,
        updates: Dict[str, Any],
    ) -> None:
        """
        更新会话状态

        Args:
            session_id: 会话ID
            tenant_id: 租户ID
            updates: 要更新的字段
        """
        state = await self.load_state(session_id, tenant_id) or {}
        state.update(updates)
        await self.save_state(session_id, tenant_id, state)

    async def delete_state(
        self,
        session_id: str,
        tenant_id: str,
    ) -> None:
        """
        删除会话状态

        Args:
            session_id: 会话ID
            tenant_id: 租户ID
        """
        key = self._make_state_key(session_id, tenant_id)
        await self.cache.delete(key)

    async def append_message(
        self,
        session_id: str,
        tenant_id: str,
        role: str,
        content: str,
    ) -> None:
        """
        添加消息到会话历史

        Args:
            session_id: 会话ID
            tenant_id: 租户ID
            role: 消息角色 (user/assistant/system)
            content: 消息内容
        """
        state = await self.load_state(session_id, tenant_id) or {}
        messages = state.get("messages", [])

        messages.append({
            "role": role,
            "content": content,
            "timestamp": asyncio.get_event_loop().time(),
        })

        # 限制历史消息数量
        if len(messages) > 100:
            messages = messages[-100:]

        state["messages"] = messages
        await self.save_state(session_id, tenant_id, state)

    def _make_state_key(self, session_id: str, tenant_id: str) -> str:
        """生成状态缓存键"""
        return f"agent:state:{tenant_id}:{session_id}"


# ============================================================================
# 全局实例
# ============================================================================

_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """获取状态管理器单例"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
