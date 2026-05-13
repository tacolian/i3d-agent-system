"""
Agent工作流定义
使用LangGraph编排多Agent协作
"""
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from .state import AgentState, create_state
from .nodes import (
    intent_node,
    retrieval_node,
    search_node,
    analysis_node,
    recommendation_node,
    qa_node,
    synthesizer_node,
    clarification_node,
)
from .edges import (
    route_after_intent,
    route_after_retrieval,
    route_after_agent,
)
from ..config import settings
from ..db.session import get_async_session


class AgentWorkflow:
    """
    Agent工作流管理器

    使用LangGraph构建多Agent协作流程:
    1. 意图识别 -> 检索 -> Agent执行 -> 综合响应
    2. 支持状态持久化（PostgreSQL）
    3. 支持流式输出
    """

    def __init__(self):
        self.graph = None
        self.checkpoint_saver = None
        self._build_graph()

    def _build_graph(self):
        """构建LangGraph工作流"""
        # 创建状态图
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("intent_classifier", intent_node)
        workflow.add_node("retrieval", retrieval_node)
        workflow.add_node("search_agent", search_node)
        workflow.add_node("analysis_agent", analysis_node)
        workflow.add_node("recommendation_agent", recommendation_node)
        workflow.add_node("qa_agent", qa_node)
        workflow.add_node("synthesizer", synthesizer_node)
        workflow.add_node("clarification", clarification_node)
    
        # 设置入口点
        workflow.set_entry_point("intent_classifier")

        # 添加边（条件路由）
        workflow.add_conditional_edges(
            "intent_classifier",
            route_after_intent,
            {
                "retrieval": "retrieval",
                "clarification": "clarification",
            }
        )

        workflow.add_conditional_edges(
            "retrieval",
            route_after_retrieval,
            {
                "search_agent": "search_agent",
                "analysis_agent": "analysis_agent",
                "recommendation_agent": "recommendation_agent",
                "qa_agent": "qa_agent",
            }
        )

        # Agent节点到综合节点
        workflow.add_edge("search_agent", "synthesizer")
        workflow.add_edge("analysis_agent", "synthesizer")
        workflow.add_edge("recommendation_agent", "synthesizer")
        workflow.add_edge("qa_agent", "synthesizer")

        # 综合节点到结束
        workflow.add_edge("synthesizer", END)
        workflow.add_edge("clarification", END)

        # 编译图
        self.graph = workflow.compile()

    async def run(
        self,
        user_input: str,
        tenant_id: str,
        session_id: str,
        request_id: str,
        max_results: int = 10,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        运行Agent工作流

        Args:
            user_input: 用户输入
            tenant_id: 租户ID
            session_id: 会话ID
            request_id: 请求ID
            max_results: 最大结果数
            stream: 是否流式返回

        Returns:
            工作流执行结果
        """
        # 创建初始状态
        initial_state = create_state(
            user_input=user_input,
            tenant_id=tenant_id,
            session_id=session_id,
            request_id=request_id,
            max_results=max_results,
        )

        # 配置（用于checkpoint）
        config = RunnableConfig(
            configurable={
                "thread_id": session_id,
                "checkpoint_ns": tenant_id,
            }
        )

        # 执行工作流
        if stream:
            # 流式执行
            async for chunk in self.graph.astream(initial_state, config):
                yield chunk
        else:
            # 一次性执行
            result = await self.graph.ainvoke(initial_state, config)
            yield result

    async def stream_events(
        self,
        user_input: str,
        tenant_id: str,
        session_id: str,
        request_id: str,
        max_results: int = 10,
    ):
        """
        流式返回工作流事件

        用于SSE/WebSocket实时推送
        """
        initial_state = create_state(
            user_input=user_input,
            tenant_id=tenant_id,
            session_id=session_id,
            request_id=request_id,
            max_results=max_results,
        )

        config = RunnableConfig(
            configurable={
                "thread_id": session_id,
                "checkpoint_ns": tenant_id,
            }
        )

        async for event in self.graph.astream_events(
            initial_state,
            config,
            version="v1",
        ):
            yield event


# ============================================================================
# 单例实例
# ============================================================================

_agent_workflow: Optional[AgentWorkflow] = None


def get_agent_workflow() -> AgentWorkflow:
    """获取Agent工作流单例"""
    global _agent_workflow
    if _agent_workflow is None:
        _agent_workflow = AgentWorkflow()
    return _agent_workflow
