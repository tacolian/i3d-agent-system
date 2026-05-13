"""
数据库会话管理
"""
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from ..config import settings


# 创建异步引擎
async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话

    用于FastAPI依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    async with async_engine.begin() as conn:
        # 创建扩展
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))

        # 创建聊天历史表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))

        # 为每个租户创建向量表
        for tenant_id in settings.SUPPORTED_TENANTS:
            table_name = f"tenant_{tenant_id}_vectors"
            await conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    chunk_id TEXT PRIMARY KEY,
                    content TEXT,
                    embedding VECTOR({settings.EMBEDDING_DIMENSION}),
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP DEFAULT NOW(),
                    item_code TEXT,
                    file_name TEXT,
                    file_path TEXT,
                    textsearchable_index_col TSVECTOR
                )
            """))

            # 创建全文搜索索引
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_textsearch
                ON {table_name}
                USING GIN (textsearchable_index_col)
            """))

            # 创建向量相似度搜索索引
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_embedding
                ON {table_name}
                USING HNSW (embedding vector_cosine_ops)
            """))


async def close_db():
    """关闭数据库连接"""
    await async_engine.dispose()
