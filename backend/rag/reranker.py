"""
重排序服务
对检索结果进行精细化排序
"""
from typing import List, Dict, Any, Optional
import time

from ..config import settings


class Reranker:
    """
    检索结果重排序器

    支持的重排序模型:
    - Cohere Rerank 3 (API)
    - BGE Reranker (本地)
    """

    def __init__(self, model: Optional[str] = None):
        """
        初始化重排序器

        Args:
            model: 重排序模型名称
        """
        self.model = model or settings.RAG_RERANKER.get("model", "cohere-rerank-v3")
        self.enabled = settings.RAG_RERANKER.get("enabled", True)

    async def rerank(
        self,
        query: str,
        results: List[Any],  # HybridSearchResult列表
        top_k: int = 5,
    ) -> List[Any]:
        """
        对检索结果进行重排序

        Args:
            query: 原始查询
            results: 检索结果列表
            top_k: 返回的top结果数量

        Returns:
            重排序后的结果列表
        """
        if not self.enabled or not results:
            return results[:top_k]

        start_time = time.time()

        # 准备候选文档文本
        documents = []
        for r in results:
            doc_text = self._prepare_document_text(r)
            documents.append(doc_text)

        # 调用重排序API
        rerank_scores = await self._compute_rerank_scores(
            query=query,
            documents=documents,
        )

        # 更新分数并重新排序
        for i, result in enumerate(results):
            if i < len(rerank_scores):
                # 将重排序分数与原始分数结合
                original_score = result.similarity
                rerank_score = rerank_scores[i]
                # 加权组合
                result.similarity = 0.3 * original_score + 0.7 * rerank_score

        # 按新分数排序
        reranked = sorted(
            results,
            key=lambda x: x.similarity,
            reverse=True,
        )

        return reranked[:top_k]

    def _prepare_document_text(self, result: Any) -> str:
        """准备用于重排序的文档文本"""
        metadata = result.metadata
        parts = []

        # 文件名
        if result.file_name:
            parts.append(f"文件名: {result.file_name}")

        # 描述
        if metadata.get("description"):
            parts.append(f"描述: {metadata['description']}")

        # 其他关键字段
        if metadata.get("category"):
            parts.append(f"分类: {metadata['category']}")

        if metadata.get("tags"):
            parts.append(f"标签: {', '.join(metadata['tags'])}")

        return " | ".join(parts)

    async def _compute_rerank_scores(
        self,
        query: str,
        documents: List[str],
    ) -> List[float]:
        """
        计算重排序分数

        Args:
            query: 查询文本
            documents: 文档文本列表

        Returns:
            重排序分数列表
        """
        # TODO: 实际调用重排序API
        # 这里返回模拟分数
        import random
        return [random.uniform(0.5, 1.0) for _ in documents]


class CohereReranker(Reranker):
    """Cohere Rerank API实现"""

    def __init__(self, api_key: str):
        super().__init__(model="cohere-rerank-v3")
        self.api_key = api_key
        self.base_url = "https://api.cohere.ai/v1/rerank"

    async def _compute_rerank_scores(
        self,
        query: str,
        documents: List[str],
    ) -> List[float]:
        """调用Cohere Rerank API"""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "documents": documents,
                    "top_n": len(documents),
                    "model": "rerank-v3",
                },
                timeout=30.0,
            )

            response.raise_for_status()
            data = response.json()

        # 提取分数
        scores = [0.0] * len(documents)
        for result in data.get("results", []):
            index = result.get("index")
            relevance_score = result.get("relevance_score", 0.0)
            if 0 <= index < len(scores):
                scores[index] = relevance_score

        return scores


class BGEReranker(Reranker):
    """BGE Reranker本地实现"""

    def __init__(self, model_path: str = "BAAI/bge-reranker-v2-m3"):
        super().__init__(model="bge-reranker-v2")
        self.model_path = model_path
        self._model = None
        self._tokenizer = None

    @property
    def model(self):
        """懒加载模型"""
        if self._model is None:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_path)
        return self._model

    async def _compute_rerank_scores(
        self,
        query: str,
        documents: List[str],
    ) -> List[float]:
        """使用BGE模型计算重排序分数"""
        # 构建查询-文档对
        pairs = [[query, doc] for doc in documents]

        # 计算分数
        scores = self.model.predict(pairs)

        # 转换为列表
        return scores.tolist()


# ============================================================================
# 全局实例
# ============================================================================

_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """获取重排序器单例"""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
