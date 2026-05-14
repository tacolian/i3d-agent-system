"""
分析Agent
负责分析CAD模型特征和属性
"""
from typing import Dict, Any, List, Optional
import time
import re

from langchain_core.messages import SystemMessage, HumanMessage

from .base import BaseAgent, AgentInput, AgentOutput
from ..models.enums import AgentType
from ..tools.file_analyzer import file_analyzer_tool


class AnalysisAgent(BaseAgent):
    """
    分析Agent

    职责:
    1. 分析CAD模型的特征和属性
    2. 提供模型的技术分析
    3. 比较不同模型的差异
    4. 提供设计建议
    """

    def __init__(self):
        super().__init__(agent_type=AgentType.ANALYSIS)

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个3D CAD模型分析专家。

你的职责是对CAD模型进行深入的技术分析。

## 分析维度

1. **几何特征**: 尺寸、形状、结构特点
2. **制造属性**: 材料、工艺、成本考虑
3. **设计评估**: 优化空间、改进建议
4. **应用场景**: 适用行业、使用环境

## 输出格式

### 模型概览
[模型的基本信息和主要特征]

### 详细分析
- 几何特征分析
- 制造工艺分析
- 设计评估

### 对比分析
[如果有多个模型，进行对比]

### 建议
[设计优化、应用建议]

## 注意事项

- 基于模型的元数据进行分析
- 如果缺少关键信息，主动询问
- 提供专业但易懂的解释
"""

    def _extract_item_code(self, query: str, search_results: List[Dict[str, Any]]) -> Optional[str]:
        """
        从查询或搜索结果中提取模型代码

        Args:
            query: 用户查询
            search_results: 搜索结果

        Returns:
            模型代码或None
        """
        # 尝试从搜索结果中获取
        if search_results and len(search_results) > 0:
            item_code = search_results[0].get("item_code")
            if item_code and item_code != "N/A":
                return item_code

        # 尝试从查询中提取（假设模型代码格式为字母+数字组合）
        # 匹配类似 "ABC-123" 或 "PART-001" 的格式
        pattern = r'[A-Za-z]+[-_]?\d+[-_]?\w*'
        matches = re.findall(pattern, query)
        if matches:
            return matches[0].upper()

        return None

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        执行分析Agent逻辑

        Args:
            input_data: Agent输入

        Returns:
            Agent输出
        """
        start_time = time.time()

        query = input_data.query
        tenant_id = input_data.tenant_id
        search_results = input_data.search_results

        # 尝试提取模型代码并调用分析工具
        analysis_data = None
        tool_used = None

        item_code = self._extract_item_code(query, search_results)
        if item_code:
            # 调用文件分析工具
            result = await file_analyzer_tool(
                item_code=item_code,
                tenant_id=tenant_id,
            )
            tool_used = "file_analyzer"

            if result.get("success"):
                analysis_data = result.get("analysis")

        # 构建消息
        additional_context = ""
        if analysis_data:
            additional_context = f"\n模型分析数据:\n{str(analysis_data)}\n使用的分析工具: {tool_used}"
        elif tool_used:
            additional_context = f"\n分析工具调用失败。使用的工具: {tool_used}"

        context = self._format_context(
            query=query,
            search_results=search_results,
            additional_context=additional_context,
        )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=context),
        ]

        # 调用LLM生成响应
        response = await self._call_llm(messages, temperature=0.6)

        # 生成分析建议
        suggestions = self._generate_analysis_suggestions(
            query=query,
            search_results=search_results,
            has_analysis=analysis_data is not None,
        )

        # 收集工具调用记录
        tool_calls = []
        if tool_used:
            tool_calls.append({
                "tool_name": tool_used,
                "arguments": {"item_code": item_code} if item_code else {},
                "result": "分析成功" if analysis_data else "分析失败",
                "duration_ms": search_results[0].get("duration_ms", 0) if tool_used == "file_analyzer" and search_results else 0,
            })

        duration = (time.time() - start_time) * 1000

        return AgentOutput(
            response=response,
            agent_type=self.agent_type,
            tool_calls=tool_calls,
            suggestions=suggestions,
            metadata={
                "duration_ms": duration,
                "analyzed_count": len(search_results),
                "item_code": item_code,
                "has_analysis": analysis_data is not None,
            },
        )

    def _generate_analysis_suggestions(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        has_analysis: bool = False,
    ) -> List[str]:
        """生成分析建议"""
        suggestions = []

        if len(search_results) == 0:
            suggestions.append("请先搜索要分析的模型")
        elif len(search_results) == 1:
            suggestions.append("可以上传相似模型进行对比分析")
            if has_analysis:
                suggestions.append("查看模型的详细参数和制造信息")
            else:
                suggestions.append("尝试提供模型代码以获取更详细的分析")
        elif len(search_results) > 1:
            suggestions.append("可以请求对不同模型进行详细对比")
            suggestions.append("询问特定方面的差异（如成本、工艺）")

        return suggestions
