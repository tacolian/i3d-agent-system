"""
向量嵌入服务
支持多种嵌入模型
"""
from typing import List, Union, Optional
import numpy as np

from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from ..config import settings


class EmbeddingService:
    """
    向量嵌入服务

    支持的模型:
    - OpenAI text-embedding-3-small
    - OpenAI text-embedding-3-large
    - BGE-M3 (通过自定义实现)
    """

    def __init__(self, model: Optional[str] = None):
        """
        初始化嵌入服务

        Args:
            model: 嵌入模型名称，默认使用配置中的模型
        """
        self.model = model or settings.EMBEDDING_MODEL
        self._embeddings: Optional[Embeddings] = None
        self._dimension = settings.EMBEDDING_DIMENSION

    @property
    def embeddings(self) -> Embeddings:
        """获取LangChain Embeddings实例"""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                model=self.model,
                openai_api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
            )
        return self._embeddings

    @property
    def dimension(self) -> int:
        """获取向量维度"""
        return self._dimension

    async def embed_text(self, text: str) -> List[float]:
        """
        对单个文本进行向量化

        Args:
            text: 输入文本

        Returns:
            向量表示
        """
        embedding = await self.embeddings.aembed_query(text)
        return embedding

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化

        Args:
            texts: 输入文本列表

        Returns:
            向量列表
        """
        embeddings = await self.embeddings.aembed_documents(texts)
        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """
        向量化查询（使用专门的查询嵌入方法）

        Args:
            query: 查询文本

        Returns:
            查询向量
        """
        return await self.embed_text(query)

    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
        method: str = "cosine",
    ) -> float:
        """
        计算两个向量的相似度

        Args:
            embedding1: 向量1
            embedding2: 向量2
            method: 相似度计算方法 (cosine, dot, euclidean)

        Returns:
            相似度分数
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        if method == "cosine":
            # 余弦相似度
            return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
        elif method == "dot":
            # 点积
            return float(np.dot(vec1, vec2))
        elif method == "euclidean":
            # 欧氏距离（转换为相似度）
            distance = np.linalg.norm(vec1 - vec2)
            return float(1 / (1 + distance))
        else:
            raise ValueError(f"Unknown similarity method: {method}")


# ============================================================================
# 全局实例
# ============================================================================

_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(model: Optional[str] = None) -> EmbeddingService:
    """获取嵌入服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model)
    return _embedding_service
