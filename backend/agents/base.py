"""
Agent基类
定义所有Agent的通用接口和行为
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import time

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ..config import settings
from ..core.llm_router import get_llm_router
from ..models.enums import AgentType


class AgentInput:
    """Agent输入"""

    def __init__(
        self,
        query: str,
        tenant_id: str,
        session_id: str,
        search_results: Optional[List[Dict[str, Any]]] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.query = query
        self.tenant_id = tenant_id
        self.session_id = session_id
        self.search_results = search_results or []
        self.context = context or ""
        self.metadata = metadata or {}


class AgentOutput:
    """Agent输出"""

    def __init__(
        self,
        response: str,
        agent_type: AgentType,
        tool_calls: List[Dict[str, Any]] = None,
        suggestions: List[str] = None,
        metadata: Dict[str, Any] = None,
        requires_clarification: bool = False,
    ):
        self.response = response
        self.agent_type = agent_type
        self.tool_calls = tool_calls or []
        self.suggestions = suggestions or []
        self.metadata = metadata or {}
        self.requires_clarification = requires_clarification

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "response": self.response,
            "agent_type": self.agent_type.value,
            "tool_calls": self.tool_calls,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
            "requires_clarification": self.requires_clarification,
        }


class BaseAgent(ABC):
    """
    Agent基类

    所有Agent都应继承此类并实现execute方法
    """

    def __init__(self, agent_type: AgentType):
        """
        初始化Agent

        Args:
            agent_type: Agent类型
        """
        self.agent_type = agent_type
        self.llm_router = get_llm_router()

    @abstractmethod
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        执行Agent逻辑

        Args:
            input_data: Agent输入

        Returns:
            Agent输出
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        获取系统提示词

        Returns:
            系统提示词字符串
        """
        pass

    async def _call_llm(
        self,
        messages: List,
        temperature: float = 0.7,
        model: Optional[str] = None,
    ) -> str:
        """
        调用LLM

        Args:
            messages: 消息列表
            temperature: 温度参数
            model: 指定模型（可选）

        Returns:
            LLM响应
        """
        start_time = time.time()

        # 如果没有指定模型，使用路由选择
        if model is None:
            llm = await self.llm_router.get_llm(
                agent_type=self.agent_type,
                messages=messages,
            )
        else:
            llm = self.llm_router.get_model_by_name(model)

        # 调用LLM
        response = await llm.ainvoke(messages)

        # 记录调用
        duration = (time.time() - start_time) * 1000

        # TODO: 记录到状态中用于监控

        if isinstance(response, AIMessage):
            return response.content
        return str(response)

    def _format_search_results(
        self,
        search_results: List[Dict[str, Any]],
        max_results: int = 5,
    ) -> str:
        """
        格式化搜索结果为上下文

        Args:
            search_results: 搜索结果列表
            max_results: 最大结果数

        Returns:
            格式化的结果字符串
        """
        if not search_results:
            return "未找到相关结果。"

        parts = []
        for i, result in enumerate(search_results[:max_results], 1):
            item_code = result.get("item_code", "N/A")
            file_name = result.get("file_name", "N/A")
            similarity = result.get("similarity", 0.0)
            metadata = result.get("metadata", {})

            part = f"{i}. {file_name} (代码: {item_code}, 相似度: {similarity:.2f})"

            if metadata.get("description"):
                part += f"\n   描述: {metadata['description']}"

            if metadata.get("category"):
                part += f"\n   分类: {metadata['category']}"

            parts.append(part)

        return "\n\n".join(parts)

    def _format_context(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        additional_context: str = "",
    ) -> str:
        """
        构建完整的上下文

        Args:
            query: 用户查询
            search_results: 搜索结果
            additional_context: 额外上下文

        Returns:
            完整上下文字符串
        """
        parts = [
            f"用户查询: {query}",
            "",
        ]

        if additional_context:
            parts.append(f"上下文信息:")
            parts.append(additional_context)
            parts.append("")

        if search_results:
            parts.append("检索结果:")
            parts.append(self._format_search_results(search_results))
            parts.append("")

        return "\n".join(parts)
