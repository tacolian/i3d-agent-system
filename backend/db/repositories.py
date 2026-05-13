"""
数据仓库层
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from .session import async_engine, AsyncSessionLocal


class VectorRepository:
    """
    向量数据仓库

    负责向量检索相关操作
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.table_name = f"tenant_{tenant_id}_vectors"

    async def vector_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        向量检索

        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            检索结果列表
        """
        async with AsyncSessionLocal() as session:
            # 构建SQL查询
            sql = f"""
                SELECT
                    item_code,
                    file_name,
                    file_path,
                    metadata,
                    1 - (embedding <=> :query_vector) as similarity
                FROM {self.table_name}
                WHERE 1=1
            """

            # 添加过滤条件
            params = {"query_vector": str(query_vector)}

            if filters:
                if filters.get("category"):
                    sql += " AND metadata->>'category' = :category"
                    params["category"] = filters["category"]
                if filters.get("tags"):
                    for tag in filters["tags"]:
                        sql += " AND :tag = ANY(metadata->'tags')"
                        params["tag"] = tag

            # 排序和限制
            sql += f" ORDER BY embedding <=> :query_vector LIMIT {top_k}"

            result = await session.execute(text(sql), params)
            rows = result.fetchall()

            return [
                {
                    "item_code": row.item_code,
                    "file_name": row.file_name,
                    "file_path": row.file_path,
                    "metadata": row.metadata,
                    "score": row.similarity,
                    "similarity": row.similarity,
                }
                for row in rows
            ]

    async def bm25_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        BM25关键词检索（简化实现）

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件

        Returns:
            检索结果列表
        """
        # 简化实现：使用全文搜索
        async with AsyncSessionLocal() as session:
            sql = f"""
                SELECT
                    item_code,
                    file_name,
                    file_path,
                    metadata,
                    ts_rank(textsearchable_index_col, to_tsquery(:query)) as score
                FROM {self.table_name}
                WHERE to_tsquery(:query) @@ textsearchable_index_col
            """

            params = {"query": " & ".join(query.split())}

            if filters:
                if filters.get("category"):
                    sql += " AND metadata->>'category' = :category"
                    params["category"] = filters["category"]

            sql += f" ORDER BY score DESC LIMIT {top_k}"

            try:
                result = await session.execute(text(sql), params)
                rows = result.fetchall()

                return [
                    {
                        "item_code": row.item_code,
                        "file_name": row.file_name,
                        "file_path": row.file_path,
                        "metadata": row.metadata,
                        "score": float(row.score) if row.score else 0.0,
                    }
                    for row in rows
                ]
            except Exception:
                # 如果全文搜索不可用，返回空结果
                return []

    async def metadata_search(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        元数据检索

        Args:
            query: 搜索查询（用于相关性）
            filters: 过滤条件
            limit: 返回结果数量

        Returns:
            检索结果列表
        """
        async with AsyncSessionLocal() as session:
            sql = f"""
                SELECT
                    item_code,
                    file_name,
                    file_path,
                    metadata
                FROM {self.table_name}
                WHERE 1=1
            """

            params = {}

            # 构建过滤条件
            if filters.get("category"):
                sql += " AND metadata->>'category' = :category"
                params["category"] = filters["category"]

            if filters.get("tags"):
                for tag in filters["tags"]:
                    sql += " AND :tag = ANY(metadata->'tags')"
                    params[f"tag_{len(params)}"] = tag

            if filters.get("date_from"):
                sql += " AND (metadata->>'created_at')::timestamp >= :date_from"
                params["date_from"] = filters["date_from"]

            if filters.get("date_to"):
                sql += " AND (metadata->>'created_at')::timestamp <= :date_to"
                params["date_to"] = filters["date_to"]

            sql += f" LIMIT {limit}"

            result = await session.execute(text(sql), params)
            rows = result.fetchall()

            return [
                {
                    "item_code": row.item_code,
                    "file_name": row.file_name,
                    "file_path": row.file_path,
                    "metadata": row.metadata,
                }
                for row in rows
            ]

    async def insert_vector(
        self,
        chunk_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """
        插入向量数据

        Args:
            chunk_id: 分块ID
            content: 文本内容
            embedding: 向量
            metadata: 元数据
        """
        async with AsyncSessionLocal() as session:
            sql = f"""
                INSERT INTO {self.table_name}
                (chunk_id, content, embedding, metadata, created_at)
                VALUES (:chunk_id, :content, :embedding, :metadata, :created_at)
                ON CONFLICT (chunk_id) DO UPDATE
                SET content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
            """

            await session.execute(
                text(sql),
                {
                    "chunk_id": chunk_id,
                    "content": content,
                    "embedding": str(embedding),
                    "metadata": metadata,
                    "created_at": datetime.now(),
                },
            )
            await session.commit()


class ChatHistoryRepository:
    """
    聊天历史仓库
    """

    async def save_message(
        self,
        session_id: str,
        tenant_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """保存聊天消息"""
        async with AsyncSessionLocal() as session:
            sql = """
                INSERT INTO chat_history
                (session_id, tenant_id, role, content, metadata, created_at)
                VALUES (:session_id, :tenant_id, :role, :content, :metadata, :created_at)
            """

            await session.execute(
                text(sql),
                {
                    "session_id": session_id,
                    "tenant_id": tenant_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata or {},
                    "created_at": datetime.now(),
                },
            )
            await session.commit()

    async def get_history(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """获取聊天历史"""
        async with AsyncSessionLocal() as session:
            sql = """
                SELECT role, content, metadata, created_at
                FROM chat_history
                WHERE session_id = :session_id AND tenant_id = :tenant_id
                ORDER BY created_at ASC
                LIMIT :limit
            """

            result = await session.execute(
                text(sql),
                {"session_id": session_id, "tenant_id": tenant_id, "limit": limit},
            )
            rows = result.fetchall()

            return [
                {
                    "role": row.role,
                    "content": row.content,
                    "metadata": row.metadata,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]
