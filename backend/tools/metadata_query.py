"""
元数据查询工具
用于基于元数据属性查询CAD模型
"""
from typing import Dict, Any, List, Optional
import time

from ..db.repositories import VectorRepository


async def metadata_query_tool(
    tenant_id: str,
    filters: Dict[str, Any],
    limit: int = 10,
) -> Dict[str, Any]:
    """
    元数据查询工具

    基于模型的元数据属性（分类、标签、创建时间等）进行查询

    Args:
        tenant_id: 租户ID
        filters: 过滤条件
        - category: 模型分类
        - tags: 标签列表
        - date_range: 时间范围
        - creator: 创建者
        limit: 返回结果数量

    Returns:
        查询结果
    """
    start_time = time.time()

    try:
        vector_repo = VectorRepository(tenant_id)

        results = await vector_repo.metadata_search(
            query="",
            filters=filters,
            limit=limit,
        )

        duration = (time.time() - start_time) * 1000

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "duration_ms": duration,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0,
            "duration_ms": (time.time() - start_time) * 1000,
        }


class MetadataQueryTool:
    """LangChain兼容的元数据查询工具"""

    name = "metadata_query"
    description = """基于元数据属性查询CAD模型。
    适用于按分类、标签、时间等属性筛选。

    输入参数:
    - tenant_id: 租户ID
    - filters: 过滤条件字典
      - category: 模型分类
      - tags: 标签列表
      - date_from: 起始日期
      - date_to: 结束日期
    - limit: 返回结果数量（默认10）

    输出:
    - 符合条件的模型列表
    """

    async def ainvoke(
        self,
        tenant_id: str,
        filters: Dict[str, Any],
        limit: int = 10,
    ) -> str:
        """异步调用工具"""
        result = await metadata_query_tool(tenant_id, filters, limit)

        if result["success"]:
            return f"找到 {result['count']} 个模型:\n" + "\n".join([
                f"- {r.get('file_name', 'N/A')}"
                for r in result["results"][:5]
            ])
        else:
            return f"查询失败: {result.get('error', 'Unknown error')}"

    def _arun(self, tenant_id: str, filters: Dict[str, Any], limit: int = 10, **kwargs):
        """LangChain工具异步运行"""
        return self.ainvoke(tenant_id, filters, limit)
