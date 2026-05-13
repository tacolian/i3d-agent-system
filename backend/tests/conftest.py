"""
Pytest配置和共享fixture
"""
import pytest
import asyncio
from typing import AsyncGenerator

from backend.db.session import AsyncSessionLocal, init_db, close_db
from backend.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def database():
    """初始化测试数据库"""
    # 使用测试数据库
    settings.DATABASE_URL = "postgresql+asyncpg://app_user:app_pass@localhost:15433/i3d_test"

    await init_db()
    yield
    await close_db()


@pytest.fixture
async def db_session(database) -> AsyncGenerator:
    """创建数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_tenant_id():
    """示例租户ID"""
    return "shenfa"


@pytest.fixture
def sample_user_input():
    """示例用户输入"""
    return "搜索一个法兰盘模型"


@pytest.fixture
def sample_search_results():
    """示例搜索结果"""
    return [
        {
            "item_code": "FLG-001",
            "file_name": "flange_150pn.dwg",
            "file_path": "/shenfa/FLG-001.dwg",
            "similarity": 0.92,
            "metadata": {
                "category": "法兰",
                "description": "DN150 PN16法兰盘",
                "tags": ["法兰", "标准件"],
            },
        },
        {
            "item_code": "FLG-002",
            "file_name": "flange_200pn.dwg",
            "file_path": "/shenfa/FLG-002.dwg",
            "similarity": 0.87,
            "metadata": {
                "category": "法兰",
                "description": "DN200 PN16法兰盘",
                "tags": ["法兰", "标准件"],
            },
        },
    ]
