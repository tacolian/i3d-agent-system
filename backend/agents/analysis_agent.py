"""
分析Agent
负责分析CAD模型特征和属性
"""
from typing import Dict, Any, List
import time

from langchain_core.messages import SystemMessage, HumanMessage

from .base import BaseAgent, AgentInput, AgentOutput
from ..models.enums import AgentType


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
        search_results = input_data.search_results

        # 构建消息
        context = self._format_context(
            query=query,
            search_results=search_results,
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
        )

        duration = (time.time() - start_time) * 1000

        return AgentOutput(
            response=response,
            agent_type=self.agent_type,
            suggestions=suggestions,
            metadata={
                "duration_ms": duration,
                "analyzed_count": len(search_results),
            },
        )

    def _generate_analysis_suggestions(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
    ) -> List[str]:
        """生成分析建议"""
        suggestions = []

        if len(search_results) == 1:
            suggestions.append("可以上传相似模型进行对比分析")
            suggestions.append("查看模型的详细参数和制造信息")
        elif len(search_results) > 1:
            suggestions.append("可以请求对不同模型进行详细对比")
            suggestions.append("询问特定方面的差异（如成本、工艺）")
        else:
            suggestions.append("请先搜索要分析的模型")

        return suggestions
