"""
Redis缓存服务
"""
from typing import Optional, Any, List
import json
import redis.asyncio as redis

from ..config import settings


class CacheService:
    """
    Redis缓存服务

    功能:
    1. 键值缓存
    2. 列表操作
    3. 集合操作
    4. 发布订阅
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    @property
    async def client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self._client is None:
            self._client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        client = await self.client
        return await client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None,
    ) -> None:
        """设置缓存值"""
        client = await self.client
        if expire:
            await client.setex(key, expire, value)
        else:
            await client.set(key, value)

    async def get_json(self, key: str) -> Optional[Any]:
        """获取JSON值"""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> None:
        """设置JSON值"""
        await self.set(key, json.dumps(value), expire)

    async def delete(self, key: str) -> None:
        """删除缓存"""
        client = await self.client
        await client.delete(key)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        client = await self.client
        return await client.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> None:
        """设置过期时间"""
        client = await self.client
        await client.expire(key, seconds)

    async def ping(self) -> bool:
        """Ping Redis"""
        try:
            client = await self.client
            return await client.ping() is True
        except:
            return False

    async def lpush(self, key: str, *values: str) -> int:
        """列表左推"""
        client = await self.client
        return await client.lpush(key, *values)

    async def rpop(self, key: str) -> Optional[str]:
        """列表右弹"""
        client = await self.client
        return await client.rpop(key)

    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """获取列表范围"""
        client = await self.client
        return await client.lrange(key, start, end)

    async def close(self) -> None:
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None


# ============================================================================
# 全局实例
# ============================================================================

_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """获取缓存服务单例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
