"""
API集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.models.schema import ChatRequest, TenantContext


@pytest.mark.asyncio
class TestChatAPI:
    """聊天API测试"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    async def test_health_check(self, client):
        """测试健康检查"""
        response = await client.get("/health/ping")
        assert response.status_code == 200
        assert response.json()["ping"] == "pong"

    async def test_chat_endpoint(self, client, sample_tenant_id):
        """测试聊天接口"""
        request_data = {
            "query": "搜索法兰盘",
            "session_id": "test-session",
            "tenant_context": {
                "tenant_id": sample_tenant_id,
            },
            "stream": False,
        }

        # 注意：实际测试需要mock AgentController
        # 这里仅验证请求格式
        response = await client.post(
            "/api/chat/",
            json=request_data,
            headers={"X-Tenant-ID": sample_tenant_id},
        )

        # 可能返回错误（因为没有真实的后端服务）
        # 但应该不是422验证错误
        assert response.status_code != 422

    async def test_invalid_tenant(self, client):
        """测试无效租户"""
        response = await client.get(
            "/health/ping",
            headers={"X-Tenant-ID": "invalid_tenant"},
        )

        # 健康检查不应该验证租户
        assert response.status_code == 200
