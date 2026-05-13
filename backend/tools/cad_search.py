"""
CAD搜索工具
用于Agent调用CAD模型搜索功能
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import httpx
import time

from ..config import settings


class CadSearchParams(BaseModel):
    """CAD搜索参数"""
    query: str = Field(..., description="搜索查询")
    tenant_id: str = Field(..., description="租户ID")
    top_k: int = Field(10, ge=1, le=50, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


async def cad_search_tool(params: CadSearchParams) -> Dict[str, Any]:
    """
    CAD模型搜索工具

    调用现有的InferEngineer-3dRetrieval服务的搜索接口

    Args:
        params: 搜索参数

    Returns:
        搜索结果
    """
    start_time = time.time()

    # 调用现有服务的API
    # 这里假设InferEngineer-3dRetrieval服务运行在18000端口
    url = f"http://localhost:18000/api/search/"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={
                    "query": params.query,
                    "tenant_id": params.tenant_id,
                    "top_k": params.top_k,
                    "filters": params.filters or {},
                },
                headers={
                    "X-Tenant-ID": params.tenant_id,
                    "Content-Type": "application/json",
                },
            )

            response.raise_for_status()
            data = response.json()

        duration = (time.time() - start_time) * 1000

        return {
            "success": True,
            "results": data.get("results", []),
            "count": len(data.get("results", [])),
            "duration_ms": duration,
            "query": params.query,
        }

    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0,
            "duration_ms": (time.time() - start_time) * 1000,
        }


# LangChain工具包装器
class CadSearchTool:
    """LangChain兼容的CAD搜索工具"""

    name = "cad_search"
    description = """搜索CAD模型数据库。
    用于查找3D模型、零件、装配体等CAD设计文件。

    输入参数:
    - query: 搜索关键词或描述
    - tenant_id: 租户ID
    - top_k: 返回结果数量（默认10）
    - filters: 可选的过滤条件（如分类、标签等）

    输出:
    - 搜索结果列表，包含文件名、相似度、元数据等
    """

    async def ainvoke(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """异步调用工具"""
        params = CadSearchParams(
            query=query,
            tenant_id=tenant_id,
            top_k=top_k,
            filters=filters,
        )

        result = await cad_search_tool(params)

        if result["success"]:
            return f"找到 {result['count']} 个结果:\n" + "\n".join([
                f"- {r.get('file_name', 'N/A')} (相似度: {r.get('similarity', 0):.2f})"
                for r in result["results"][:5]
            ])
        else:
            return f"搜索失败: {result.get('error', 'Unknown error')}"

    def _arun(self, query: str, tenant_id: str, top_k: int = 10, **kwargs):
        """LangChain工具异步运行"""
        return self.ainvoke(query, tenant_id, top_k, kwargs.get("filters"))
