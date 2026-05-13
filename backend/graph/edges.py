"""
LangGraph边定义（条件路由）
定义节点之间的转换逻辑
"""
from typing import Literal
from .state import AgentState


# ============================================================================
# 意图识别后的路由
# ============================================================================

def route_after_intent(state: AgentState) -> Literal["retrieval", "clarification"]:
    """
    意图识别后的路由决策

    路由规则:
    - 置信度 >= 0.7 -> 执行检索
    - 置信度 < 0.7 -> 请求澄清
    """
    confidence = state["intent_confidence"]

    if confidence >= 0.7:
        return "retrieval"
    else:
        return "clarification"


# ============================================================================
# 检索后的路由
# ============================================================================

def route_after_retrieval(state: AgentState) -> Literal[
    "search_agent",
    "analysis_agent",
    "recommendation_agent",
    "qa_agent",
    "synthesizer",
]:
    """
    检索后的Agent选择路由

    路由规则:
    - search/similarity -> search_agent
    - analysis -> analysis_agent
    - recommendation -> recommendation_agent
    - qa/unknown -> qa_agent
    """
    intent = state["intent"]

    if intent == "search" or intent == "similarity":
        return "search_agent"
    elif intent == "analysis":
        return "analysis_agent"
    elif intent == "recommendation":
        return "recommendation_agent"
    else:
        return "qa_agent"


# ============================================================================
# Agent执行后的路由
# ============================================================================

def route_after_agent(state: AgentState) -> Literal["end", "clarification"]:
    """
    Agent执行后的路由决策

    路由规则:
    - 如果Agent标记需要澄清 -> clarification
    - 否则 -> end
    """
    if state.get("requires_clarification", False):
        return "clarification"
    return "end"


# ============================================================================
# 多Agent协调路由
# ============================================================================

def should_continue(state: AgentState) -> bool:
    """
    判断是否需要继续执行更多Agent

    条件:
    - 已执行的Agent数量 < 3
    - 且没有错误
    - 且不需要澄清
    """
    executed_agents = len(state["agent_outputs"])
    has_error = state.get("error") is not None
    needs_clarification = state.get("requires_clarification", False)

    return executed_agents < 3 and not has_error and not needs_clarification


def next_agent(state: AgentState) -> str:
    """
    选择下一个执行的Agent

    策略:
    1. 如果已执行search_agent -> analysis_agent
    2. 如果已执行analysis_agent -> recommendation_agent
    3. 否则 -> qa_agent
    """
    executed = set(state["agent_outputs"].keys())

    if "search_agent" not in executed:
        return "search_agent"
    elif "analysis_agent" not in executed:
        return "analysis_agent"
    elif "recommendation_agent" not in executed:
        return "recommendation_agent"
    else:
        return "qa_agent"
