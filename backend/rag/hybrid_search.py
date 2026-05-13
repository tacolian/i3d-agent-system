"""
混合检索实现
结合BM25关键词检索和向量语义检索
"""
from typing import List, Dict, Any, Optional, Tuple
import time

from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document

from .embeddings import get_embedding_service
from .reranker import get_reranker
from ..config import settings
from ..db.repositories import VectorRepository


class HybridSearchResult:
    """混合检索结果"""

    def __init__(
        self,
        item_code: str,
        file_name: str,
        file_path: str,
        similarity: float,
        metadata: Dict[str, Any],
        bm25_score: float = 0.0,
        vector_score: float = 0.0,
    ):
        self.item_code = item_code
        self.file_name = file_name
        self.file_path = file_path
        self.similarity = similarity
        self.metadata = metadata
        self.bm25_score = bm25_score
        self.vector_score = vector_score

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "item_code": self.item_code,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "similarity": self.similarity,
            "metadata": self.metadata,
            "bm25_score": self.bm25_score,
            "vector_score": self.vector_score,
        }


async def hybrid_search(
    query: str,
    tenant_id: str,
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    use_reranker: bool = True,
) -> List[Dict[str, Any]]:
    """
    执行混合检索

    流程:
    1. 并行执行BM25和向量检索
    2. 按权重合并结果
    3. 可选：使用重排序模型
    4. 返回top-k结果

    Args:
        query: 查询文本
        tenant_id: 租户ID
        top_k: 返回结果数量
        filters: 元数据过滤条件
        use_reranker: 是否使用重排序

    Returns:
        检索结果列表
    """
    start_time = time.time()

    # 1. 并行执行BM25和向量检索
    vector_repo = VectorRepository(tenant_id)

    # 向量检索
    embedding_service = get_embedding_service()
    query_vector = await embedding_service.embed_query(query)

    vector_results = await vector_repo.vector_search(
        query_vector=query_vector,
        top_k=top_k * 2,  # 获取更多候选
        filters=filters,
    )

    # BM25检索（简化实现，实际应该使用专门的BM25库）
    bm25_results = await vector_repo.bm25_search(
        query=query,
        top_k=top_k * 2,
        filters=filters,
    )

    # 2. 合并结果
    combined_results = _merge_results(
        vector_results=vector_results,
        bm25_results=bm25_results,
        vector_weight=settings.RAG_VECTOR_WEIGHT,
        bm25_weight=settings.RAG_BM25_WEIGHT,
    )

    # 3. 过滤低分结果
    filtered_results = [
        r for r in combined_results
        if r.similarity >= settings.RAG_SIMILARITY_THRESHOLD
    ]

    # 4. 重排序（如果启用）
    if use_reranker and filtered_results:
        reranker = get_reranker()
        reranked_results = await reranker.rerank(
            query=query,
            results=filtered_results,
            top_k=settings.RAG_RERANK_TOP_K,
        )
        final_results = reranked_results
    else:
        final_results = filtered_results[:top_k]

    # 记录延迟
    latency = (time.time() - start_time) * 1000

    return [r.to_dict() for r in final_results]


def _merge_results(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    vector_weight: float,
    bm25_weight: float,
) -> List[HybridSearchResult]:
    """
    合并向量检索和BM25检索结果

    使用加权分数合并:
    final_score = vector_weight * vector_score + bm25_weight * bm25_score
    """
    # 创建结果映射 (item_code -> result)
    results_map: Dict[str, HybridSearchResult] = {}

    # 处理向量检索结果
    for vr in vector_results:
        item_code = vr.get("item_code")
        if item_code not in results_map:
            results_map[item_code] = HybridSearchResult(
                item_code=item_code,
                file_name=vr.get("file_name", ""),
                file_path=vr.get("file_path", ""),
                similarity=0.0,
                metadata=vr.get("metadata", {}),
                vector_score=vr.get("score", 0.0),
            )
        else:
            results_map[item_code].vector_score = vr.get("score", 0.0)

    # 处理BM25检索结果
    for br in bm25_results:
        item_code = br.get("item_code")
        if item_code not in results_map:
            results_map[item_code] = HybridSearchResult(
                item_code=item_code,
                file_name=br.get("file_name", ""),
                file_path=br.get("file_path", ""),
                similarity=0.0,
                metadata=br.get("metadata", {}),
                bm25_score=br.get("score", 0.0),
            )
        else:
            results_map[item_code].bm25_score = br.get("score", 0.0)

    # 计算加权分数
    for result in results_map.values():
        # 归一化分数到 [0, 1]
        normalized_vector = min(result.vector_score, 1.0)
        normalized_bm25 = min(result.bm25_score, 1.0)

        result.similarity = (
            vector_weight * normalized_vector +
            bm25_weight * normalized_bm25
        )

    # 按分数排序
    return sorted(
        results_map.values(),
        key=lambda x: x.similarity,
        reverse=True,
    )


class HybridRetriever(BaseRetriever):
    """
    LangChain兼容的混合检索器
    """

    def __init__(
        self,
        tenant_id: str,
        top_k: int = 10,
        use_reranker: bool = True,
    ):
        super().__init__()
        self.tenant_id = tenant_id
        self.top_k = top_k
        self.use_reranker = use_reranker

    def _get_relevant_documents(
        self,
        query: str,
        run_id: Optional[str] = None,
    ) -> List[Document]:
        """
        获取相关文档

        Args:
            query: 查询文本
            run_id: 运行ID

        Returns:
            文档列表
        """
        # 这是一个同步方法，实际应该使用异步
        # 这里简化实现
        results = []

        # TODO: 实现同步版本的混合检索
        # 或者使用asyncio.run()

        return results

    async def aget_relevant_documents(
        self,
        query: str,
        run_id: Optional[str] = None,
    ) -> List[Document]:
        """
        异步获取相关文档

        Args:
            query: 查询文本
            run_id: 运行ID

        Returns:
            文档列表
        """
        results_dicts = await hybrid_search(
            query=query,
            tenant_id=self.tenant_id,
            top_k=self.top_k,
            use_reranker=self.use_reranker,
        )

        documents = []
        for r in results_dicts:
            doc = Document(
                page_content=r.get("metadata", {}).get("description", ""),
                metadata={
                    "item_code": r["item_code"],
                    "file_name": r["file_name"],
                    "file_path": r["file_path"],
                    "similarity": r["similarity"],
                    **r.get("metadata", {}),
                },
            )
            documents.append(doc)

        return documents
