"""
RAG检索器实现
支持多种检索策略
"""
from typing import List, Dict, Any, Optional
from enum import Enum

from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document

from .hybrid_search import HybridRetriever
from .embeddings import get_embedding_service
from ..config import settings


class RetrievalStrategy(str, Enum):
    """检索策略"""
    VECTOR = "vector"           # 纯向量检索
    HYBRID = "hybrid"           # 混合检索 (BM25 + Vector)
    METADATA = "metadata"       # 元数据检索
    SEMANTIC = "semantic"       # 语义检索


class Retriever:
    """
    统一检索接口

    根据配置自动选择最佳检索策略
    """

    def __init__(
        self,
        tenant_id: str,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        top_k: int = 10,
    ):
        """
        初始化检索器

        Args:
            tenant_id: 租户ID
            strategy: 检索策略
            top_k: 返回结果数量
        """
        self.tenant_id = tenant_id
        self.strategy = strategy
        self.top_k = top_k
        self._langchain_retriever: Optional[BaseRetriever] = None

    @property
    def langchain_retriever(self) -> BaseRetriever:
        """获取LangChain兼容的检索器"""
        if self._langchain_retriever is None:
            self._langchain_retriever = HybridRetriever(
                tenant_id=self.tenant_id,
                top_k=self.top_k,
            )
        return self._langchain_retriever

    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        执行检索

        Args:
            query: 查询文本
            filters: 元数据过滤条件

        Returns:
            检索到的文档列表
        """
        if self.strategy == RetrievalStrategy.HYBRID:
            return await self._hybrid_retrieve(query, filters)
        elif self.strategy == RetrievalStrategy.VECTOR:
            return await self._vector_retrieve(query, filters)
        elif self.strategy == RetrievalStrategy.METADATA:
            return await self._metadata_retrieve(query, filters)
        else:
            return await self._hybrid_retrieve(query, filters)

    async def _hybrid_retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """混合检索"""
        retriever = HybridRetriever(
            tenant_id=self.tenant_id,
            top_k=self.top_k,
        )
        return await retriever.aget_relevant_documents(query)

    async def _vector_retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """纯向量检索"""
        from ..db.repositories import VectorRepository

        embedding_service = get_embedding_service()
        query_vector = await embedding_service.embed_query(query)

        vector_repo = VectorRepository(self.tenant_id)
        results = await vector_repo.vector_search(
            query_vector=query_vector,
            top_k=self.top_k,
            filters=filters,
        )

        documents = []
        for r in results:
            doc = Document(
                page_content=r.get("metadata", {}).get("description", ""),
                metadata={
                    "item_code": r.get("item_code"),
                    "file_name": r.get("file_name"),
                    "similarity": r.get("score", 0.0),
                    **r.get("metadata", {}),
                },
            )
            documents.append(doc)

        return documents

    async def _metadata_retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """元数据检索"""
        from ..db.repositories import VectorRepository

        vector_repo = VectorRepository(self.tenant_id)
        results = await vector_repo.metadata_search(
            query=query,
            filters=filters or {},
            limit=self.top_k,
        )

        documents = []
        for r in results:
            doc = Document(
                page_content=r.get("metadata", {}).get("description", ""),
                metadata={
                    "item_code": r.get("item_code"),
                    "file_name": r.get("file_name"),
                    **r.get("metadata", {}),
                },
            )
            documents.append(doc)

        return documents


# ============================================================================
# 工厂函数
# ============================================================================

def create_retriever(
    tenant_id: str,
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
    top_k: int = 10,
) -> Retriever:
    """
    创建检索器实例

    Args:
        tenant_id: 租户ID
        strategy: 检索策略
        top_k: 返回结果数量

    Returns:
        检索器实例
    """
    return Retriever(
        tenant_id=tenant_id,
        strategy=strategy,
        top_k=top_k,
    )
