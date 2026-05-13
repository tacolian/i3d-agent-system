"""
LangGraph状态定义
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Agent状态定义
    用于LangGraph工作流中的状态传递
    """
    # 基础输入
    user_input: str
    tenant_id: str
    session_id: str
    request_id: str
    max_results: int

    # 消息历史（带注解，自动合并）
    messages: Annotated[List[BaseMessage], add_messages]

    # 意图识别
    intent: str
    intent_confidence: float
    intent_reasoning: str

    # 搜索相关
    search_params: Optional[Dict[str, Any]]
    search_results: List[Dict[str, Any]]
    retrieval_context: str

    # Agent执行
    active_agent: str
    agent_outputs: Dict[str, str]

    # 工具调用
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]

    # 最终输出
    response: str
    response_type: str
    suggestions: List[str]
    requires_clarification: bool

    # 中间步骤
    intermediate_steps: List[Dict[str, Any]]

    # 性能指标
    latency: Dict[str, float]
    llm_calls: List[Dict[str, Any]]

    # 错误处理
    error: Optional[str]
    retry_count: int


def create_state(
    user_input: str,
    tenant_id: str,
    session_id: str,
    request_id: str,
    max_results: int = 10,
) -> AgentState:
    """
    创建初始Agent状态

    Args:
        user_input: 用户输入
        tenant_id: 租户ID
        session_id: 会话ID
        request_id: 请求ID
        max_results: 最大结果数

    Returns:
        AgentState: 初始化的状态对象
    """
    return AgentState(
        # 基础输入
        user_input=user_input,
        tenant_id=tenant_id,
        session_id=session_id,
        request_id=request_id,
        max_results=max_results,

        # 消息历史
        messages=[],

        # 意图识别
        intent="unknown",
        intent_confidence=0.0,
        intent_reasoning="",

        # 搜索相关
        search_params=None,
        search_results=[],
        retrieval_context="",

        # Agent执行
        active_agent="",
        agent_outputs={},

        # 工具调用
        tool_calls=[],
        tool_results=[],

        # 最终输出
        response="",
        response_type="answer",
        suggestions=[],
        requires_clarification=False,

        # 中间步骤
        intermediate_steps=[],

        # 性能指标
        latency={},
        llm_calls=[],

        # 错误处理
        error=None,
        retry_count=0,
    )


def update_state_metrics(state: AgentState, phase: str, duration_ms: float) -> AgentState:
    """更新状态中的性能指标"""
    state["latency"][phase] = state["latency"].get(phase, 0) + duration_ms
    return state


def add_llm_call(
    state: AgentState,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    latency_ms: float,
) -> AgentState:
    """添加LLM调用记录"""
    state["llm_calls"].append({
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
    })
    return state
