"""
问答Agent
负责回答用户关于CAD模型和系统的问题
"""
from typing import Dict, Any, List
import time

from langchain_core.messages import SystemMessage, HumanMessage

from .base import BaseAgent, AgentInput, AgentOutput
from ..models.enums import AgentType


class QAAgent(BaseAgent):
    """
    问答Agent

    职责:
    1. 回答用户关于CAD模型的各类问题
    2. 解释技术概念和术语
    3. 提供操作指导
    4. 解答系统使用问题
    """

    def __init__(self):
        super().__init__(agent_type=AgentType.QA)

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个3D CAD智能检索系统的问答助手。

你的职责是回答用户关于CAD模型、设计制造、系统使用的各类问题。

## 能力范围

1. **模型相关**: 模型特征、参数、应用场景
2. **技术问题**: CAD设计、制造工艺、材料选择
3. **系统使用**: 搜索技巧、功能说明、操作指导
4. **行业知识**: 设计规范、标准、最佳实践

## 回答原则

1. **准确**: 基于检索到的信息回答，不确定时说明
2. **简洁**: 直接回答问题，避免冗余
3. **结构化**: 使用列表、分点等方式组织信息
4. **友好**: 语气亲切，主动提供额外帮助

## 输出格式

### 直接回答
[清晰、准确地回答用户的问题]

### 补充信息
[提供相关的背景信息或延伸知识]

### 相关建议
[如果适用，提供操作建议或下一步指引]

## 注意事项

- 如果检索结果包含答案，基于结果回答
- 如果检索结果不足，说明并建议用户提供更多信息
- 对于技术问题，提供专业但易懂的解释
- 对于操作问题，提供步骤化的指导
"""

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        执行问答Agent逻辑

        Args:
            input_data: Agent输入

        Returns:
            Agent输出
        """
        start_time = time.time()

        query = input_data.query
        search_results = input_data.search_results
        context = input_data.context

        # 构建消息
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=self._format_context(
                query=query,
                search_results=search_results,
                additional_context=context,
            )),
        ]

        # 调用LLM生成响应
        response = await self._call_llm(messages, temperature=0.7)

        # 生成后续建议
        suggestions = self._generate_qa_suggestions(
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
                "context_used": bool(context or search_results),
            },
        )

    def _generate_qa_suggestions(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
    ) -> List[str]:
        """生成问答建议"""
        suggestions = []

        # 基于问题类型的建议
        question_lower = query.lower()

        if any(word in question_lower for word in ["如何", "怎么", "how"]):
            suggestions.append("如果需要更详细的步骤指导，请告诉我")
            suggestions.append("可以查看相关模型的操作文档")

        elif any(word in question_lower for word in ["什么", "是什么", "what", "定义"]):
            suggestions.append("可以询问相关的应用场景")
            suggestions.append("了解相关的技术标准可能有帮助")

        elif any(word in question_lower for word in ["为什么", "why", "原因"]):
            suggestions.append("可以深入探讨技术细节")
            suggestions.append("查看相关的最佳实践")

        # 如果有搜索结果
        if search_results:
            suggestions.append("可以点击查看相关模型的详细信息")
            suggestions.append("询问关于这些模型的更多细节")

        return suggestions
