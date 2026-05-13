"""
推荐Agent
负责提供CAD模型推荐和设计建议
"""
from typing import Dict, Any, List
import time

from langchain_core.messages import SystemMessage, HumanMessage

from .base import BaseAgent, AgentInput, AgentOutput
from ..models.enums import AgentType


class RecommendationAgent(BaseAgent):
    """
    推荐Agent

    职责:
    1. 基于用户需求推荐合适的CAD模型
    2. 提供设计优化建议
    3. 推荐相似或相关的模型
    4. 提供选型指导
    """

    def __init__(self):
        super().__init__(agent_type=AgentType.RECOMMENDATION)

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个3D CAD模型推荐专家。

你的职责是为用户提供智能的模型推荐和选型建议。

## 推荐策略

1. **需求匹配**: 根据应用场景推荐最合适的模型
2. **相似推荐**: 基于当前模型推荐相似替代品
3. **优化建议**: 推荐设计改进方案
4. **配套推荐**: 推荐相关的装配体和零件

## 输出格式

### 需求分析
[分析用户的具体需求和应用场景]

### 推荐模型
[列出推荐的模型，说明推荐理由]

### 对比说明
[对比不同选项的优缺点]

### 选型建议
[给出最终的选型建议和理由]

## 注意事项

- 优先推荐高相似度、高质量的模型
- 说明推荐理由（为什么推荐这个）
- 考虑成本、可制造性等实际因素
- 如果信息不足，主动询问关键需求
"""

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        执行推荐Agent逻辑

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
            additional_context=input_data.context,
        )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=context),
        ]

        # 调用LLM生成响应
        response = await self._call_llm(messages, temperature=0.7)

        # 生成推荐建议
        suggestions = self._generate_recommendation_suggestions(
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
                "recommended_count": len(search_results),
            },
        )

    def _generate_recommendation_suggestions(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
    ) -> List[str]:
        """生成推荐建议"""
        suggestions = []

        if search_results:
            top_results = [r for r in search_results if r.get("similarity", 0) > 0.8]
            if top_results:
                suggestions.append("查看高相似度模型的详细参数")
                suggestions.append("可以请求对比推荐的几个模型")
            else:
                suggestions.append("尝试调整搜索条件以获得更好的推荐")

        suggestions.append("告诉我更多应用场景以获得更精准的推荐")
        suggestions.append("可以上传参考图片或模型进行相似推荐")

        return suggestions
