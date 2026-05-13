"""
Agent控制器
统一管理Agent的执行和协调
"""
from typing import Dict, Any, List, Optional, AsyncIterator
import time
import uuid

from langchain_core.messages import AIMessage, HumanMessage

from ..graph.workflow import get_agent_workflow
from ..models.schema import (
    ChatRequest,
    AgentResponse,
    ToolCall,
    LatencyMetrics,
    LLMCall,
    StreamChunk,
)
from ..models.enums import IntentType, ResponseType, AgentType
from ..config import settings


class AgentController:
    """
    Agent控制器

    职责:
    1. 接收用户请求
    2. 调用LangGraph工作流
    3. 管理Agent执行
    4. 处理流式响应
    5. 收集指标
    """

    def __init__(self):
        self.workflow = get_agent_workflow()

    async def process_request(
        self,
        request: ChatRequest,
    ) -> AgentResponse:
        """
        处理聊天请求（非流式）

        Args:
            request: 聊天请求

        Returns:
            Agent响应
        """
        start_time = time.time()
        request_id = request.tenant_context.request_id or str(uuid.uuid4())

        # 运行工作流
        final_state = None
        async for state in self.workflow.run(
            user_input=request.query,
            tenant_id=request.tenant_context.tenant_id,
            session_id=request.session_id or str(uuid.uuid4()),
            request_id=request_id,
            max_results=request.max_results,
            stream=False,
        ):
            final_state = state

        # 构建响应
        return self._build_response(
            state=final_state,
            request_id=request_id,
            session_id=request.session_id or str(uuid.uuid4()),
            start_time=start_time,
        )

    async def process_request_stream(
        self,
        request: ChatRequest,
    ) -> AsyncIterator[StreamChunk]:
        """
        处理聊天请求（流式）

        Args:
            request: 聊天请求

        Yields:
            流式响应块
        """
        start_time = time.time()
        request_id = request.tenant_context.request_id or str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())

        # 发送开始元数据
        yield StreamChunk(
            chunk_type="metadata",
            metadata={
                "request_id": request_id,
                "session_id": session_id,
                "timestamp": time.time(),
            },
        )

        # 流式运行工作流
        async for state in self.workflow.run(
            user_input=request.query,
            tenant_id=request.tenant_context.tenant_id,
            session_id=session_id,
            request_id=request_id,
            max_results=request.max_results,
            stream=True,
        ):
            # 发送内容块
            if state.get("response"):
                yield StreamChunk(
                    chunk_type="content",
                    content=state.get("response", ""),
                )

            # 发送工具调用信息
            if state.get("tool_calls"):
                for tool_call in state["tool_calls"]:
                    yield StreamChunk(
                        chunk_type="tool_call",
                        tool_call=ToolCall(**tool_call),
                    )

        # 发送结束标记
        yield StreamChunk(
            chunk_type="metadata",
            metadata={"complete": True},
            is_final=True,
        )

    def _build_response(
        self,
        state: Dict[str, Any],
        request_id: str,
        session_id: str,
        start_time: float,
    ) -> AgentResponse:
        """构建Agent响应"""
        total_latency = (time.time() - start_time) * 1000

        # 提取工具调用
        tool_calls = [
            ToolCall(
                tool_name=tc.get("tool_name"),
                arguments=tc.get("arguments", {}),
                result=tc.get("result"),
                error=tc.get("error"),
                duration_ms=tc.get("duration_ms", 0),
            )
            for tc in state.get("tool_calls", [])
        ]

        # 提取LLM调用
        llm_calls = [
            LLMCall(
                model=call.get("model"),
                prompt_tokens=call.get("prompt_tokens", 0),
                completion_tokens=call.get("completion_tokens", 0),
                total_tokens=call.get("total_tokens", 0),
                cost_usd=call.get("cost_usd", 0.0),
                latency_ms=call.get("latency_ms", 0.0),
            )
            for call in state.get("llm_calls", [])
        ]

        # 构建延迟指标
        latency = LatencyMetrics(
            total_ms=total_latency,
            intent_classification_ms=state.get("latency", {}).get("intent_classification", 0),
            routing_ms=state.get("latency", {}).get("routing", 0),
            retrieval_ms=state.get("latency", {}).get("retrieval", 0),
            generation_ms=state.get("latency", {}).get("generation", 0),
            tool_calls_ms=state.get("latency", {}).get("tool_calls", 0),
        )

        return AgentResponse(
            response=state.get("response", "抱歉，我无法处理您的请求。"),
            response_type=ResponseType(state.get("response_type", "answer")),
            intent=IntentType(state.get("intent", "unknown")),
            intent_confidence=state.get("intent_confidence", 0.0),
            agent_used=AgentType(state.get("active_agent", "qa_agent")),
            tool_calls=tool_calls,
            search_results=state.get("search_results", []),
            llm_calls=llm_calls,
            latency=latency,
            session_id=session_id,
            requires_clarification=state.get("requires_clarification", False),
            suggestions=state.get("suggestions", []),
        )


# ============================================================================
# 全局实例
# ============================================================================

_agent_controller: Optional[AgentController] = None


def get_agent_controller() -> AgentController:
    """获取Agent控制器单例"""
    global _agent_controller
    if _agent_controller is None:
        _agent_controller = AgentController()
    return _agent_controller
