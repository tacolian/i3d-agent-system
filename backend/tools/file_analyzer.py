"""
文件分析工具
用于分析CAD模型文件的详细信息
"""
from typing import Dict, Any, List, Optional
import time
import httpx


async def file_analyzer_tool(
    item_code: str,
    tenant_id: str,
) -> Dict[str, Any]:
    """
    文件分析工具

    获取CAD模型的详细分析信息，包括:
    - 几何特征
    - 参数规格
    - 制造信息
    - 使用历史

    Args:
        item_code: 模型代码
        tenant_id: 租户ID

    Returns:
        分析结果
    """
    start_time = time.time()

    try:
        # 调用3d-search-core服务获取模型分析
        url = f"http://localhost:28000/api/analysis/{item_code}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                url,
                headers={"X-Tenant-ID": tenant_id},
            )

            response.raise_for_status()
            data = response.json()

        duration = (time.time() - start_time) * 1000

        return {
            "success": True,
            "item_code": item_code,
            "analysis": data,
            "duration_ms": duration,
        }

    except httpx.HTTPError as e:
        # 如果API调用失败，返回基本信息
        return {
            "success": False,
            "item_code": item_code,
            "error": str(e),
            "duration_ms": (time.time() - start_time) * 1000,
        }


class FileAnalyzerTool:
    """LangChain兼容的文件分析工具"""

    name = "file_analyzer"
    description = """分析CAD模型文件的详细信息。
    获取模型的几何特征、参数规格、制造信息等。

    输入参数:
    - item_code: 模型代码
    - tenant_id: 租户ID

    输出:
    - 模型的详细分析信息
    """

    async def ainvoke(
        self,
        item_code: str,
        tenant_id: str,
    ) -> str:
        """异步调用工具"""
        result = await file_analyzer_tool(item_code, tenant_id)

        if result["success"]:
            analysis = result["analysis"]
            parts = [
                f"模型代码: {item_code}",
                f"文件名: {analysis.get('file_name', 'N/A')}",
                f"分类: {analysis.get('category', 'N/A')}",
            ]

            if analysis.get("geometry"):
                parts.append("\n几何特征:")
                for k, v in analysis["geometry"].items():
                    parts.append(f"  {k}: {v}")

            if analysis.get("parameters"):
                parts.append("\n参数规格:")
                for k, v in analysis["parameters"].items():
                    parts.append(f"  {k}: {v}")

            return "\n".join(parts)
        else:
            return f"分析失败: {result.get('error', 'Unknown error')}"

    def _arun(self, item_code: str, tenant_id: str, **kwargs):
        """LangChain工具异步运行"""
        return self.ainvoke(item_code, tenant_id)
