"""
相似度搜索工具
用于基于向量相似度搜索CAD模型
"""
from typing import Dict, Any, List, Optional
import time

from ..rag.hybrid_search import hybrid_search


async def similarity_search_tool(
    query: str,
    tenant_id: str,
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    相似度搜索工具

    使用向量检索查找与查询语义相似的CAD模型

    Args:
        query: 搜索查询
        tenant_id: 租户ID
        top_k: 返回结果数量
        filters: 过滤条件

    Returns:
        搜索结果
    """
    start_time = time.time()

    try:
        results = await hybrid_search(
            query=query,
            tenant_id=tenant_id,
            top_k=top_k,
            filters=filters,
            use_reranker=True,
        )

        duration = (time.time() - start_time) * 1000

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "duration_ms": duration,
            "query": query,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0,
            "duration_ms": (time.time() - start_time) * 1000,
        }


class SimilaritySearchTool:
    """LangChain兼容的相似度搜索工具"""

    name = "similarity_search"
    description = """基于语义相似度搜索CAD模型。
    适用于描述性查询，如"查找类似法兰盘的零件"。

    输入参数:
    - query: 描述性查询文本
    - tenant_id: 租户ID
    - top_k: 返回结果数量（默认10）

    输出:
    - 按相似度排序的模型列表
    """

    async def ainvoke(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 10,
    ) -> str:
        """异步调用工具"""
        result = await similarity_search_tool(query, tenant_id, top_k)

        if result["success"]:
            return f"找到 {result['count']} 个相似模型:\n" + "\n".join([
                f"- {r.get('file_name', 'N/A')} (相似度: {r.get('similarity', 0):.2f})"
                for r in result["results"][:5]
            ])
        else:
            return f"搜索失败: {result.get('error', 'Unknown error')}"

    def _arun(self, query: str, tenant_id: str, top_k: int = 10, **kwargs):
        """LangChain工具异步运行"""
        return self.ainvoke(query, tenant_id, top_k)
