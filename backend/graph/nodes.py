"""
LangGraph节点定义
每个节点代表Agent工作流中的一个处理步骤
"""
import time
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from .state import AgentState, create_state, update_state_metrics
from ..agents.search_agent import SearchAgent
from ..agents.analysis_agent import AnalysisAgent
from ..agents.recommendation_agent import RecommendationAgent
from ..agents.qa_agent import QAAgent
from ..agents.base import AgentInput
from ..config import settings


# ============================================================================
# 意图识别节点
# ============================================================================

async def intent_node(state: AgentState) -> AgentState:
    """
    意图识别节点
    分析用户输入，确定用户意图和置信度
    """
    start_time = time.time()

    user_input = state["user_input"]
    tenant_id = state["tenant_id"]

    # TODO: 实际应该调用意图识别LLM
    # 这里简化为基于规则的关键词匹配
    intent_keywords = {
        "search": ["搜索", "查找", "找", "search", "find"],
        "similarity": ["相似", "类似", "similar"],
        "analysis": ["分析", "特点", "特征", "analyze"],
        "recommendation": ["推荐", "建议", "recommend"],
        "qa": ["什么", "如何", "怎么", "是什么", "what", "how"],
    }

    intent = "unknown"
    confidence = 0.0
    reasoning = ""

    for intent_type, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in user_input.lower():
                intent = intent_type
                confidence = 0.8
                reasoning = f"检测到关键词: {keyword}"
                break
        if intent != "unknown":
            break

    # 更新状态
    state["intent"] = intent
    state["intent_confidence"] = confidence
    state["intent_reasoning"] = reasoning

    # 添加消息
    state["messages"].append(AIMessage(
        content=f"意图识别: {intent} (置信度: {confidence})",
    ))

    # 更新延迟指标
    duration = (time.time() - start_time) * 1000
    state = update_state_metrics(state, "intent_classification", duration)

    return state


# ============================================================================
# 检索节点
# ============================================================================

async def retrieval_node(state: AgentState) -> AgentState:
    """
    检索节点
    根据意图执行相应的检索操作
    """
    start_time = time.time()

    intent = state["intent"]
    user_input = state["user_input"]
    tenant_id = state["tenant_id"]
    max_results = state["max_results"]

    # 构建搜索参数
    search_params = {
        "query": user_input,
        "tenant_id": tenant_id,
        "top_k": max_results,
        "filters": {},
    }

    state["search_params"] = search_params

    # 根据意图执行检索
    if intent in ["search", "similarity", "unknown"]:
        # 执行向量检索
        from ..rag.hybrid_search import hybrid_search

        results = await hybrid_search(
            query=user_input,
            tenant_id=tenant_id,
            top_k=max_results,
        )

        state["search_results"] = results
        state["retrieval_context"] = _format_results_as_context(results)

    # 更新延迟指标
    duration = (time.time() - start_time) * 1000
    state = update_state_metrics(state, "retrieval", duration)

    return state


def _format_results_as_context(results: List[Dict[str, Any]]) -> str:
    """将搜索结果格式化为上下文字符串"""
    if not results:
        return "未找到相关结果。"

    context_parts = []
    for i, result in enumerate(results[:5], 1):
        context_parts.append(
            f"{i}. {result.get('file_name', 'N/A')} "
            f"(相似度: {result.get('similarity', 0):.2f})"
        )

    return "检索结果:\n" + "\n".join(context_parts)


# ============================================================================
# Agent执行节点
# ============================================================================

async def search_node(state: AgentState) -> AgentState:
    """搜索Agent节点"""
    start_time = time.time()

    agent = SearchAgent()
    result = await agent.execute(
        AgentInput(
            query=state["user_input"],
            tenant_id=state["tenant_id"],
            session_id=state["session_id"],
            search_results=state["search_results"],
        )
    )

    state["agent_outputs"]["search"] = result["response"]
    state["active_agent"] = "search_agent"
    state["response"] = result["response"]
    state["response_type"] = "search_results"
    state["suggestions"] = result.get("suggestions", [])

    duration = (time.time() - start_time) * 1000
    state = update_state_metrics(state, "agent_execution", duration)

    state["messages"].append(AIMessage(content=result["response"]))

    return state


async def analysis_node(state: AgentState) -> AgentState:
    """分析Agent节点"""
    start_time = time.time()

    agent = AnalysisAgent()
    result = await agent.execute(
        AgentInput(
            query=state["user_input"],
            tenant_id=state["tenant_id"],
            session_id=state["session_id"],
            search_results=state["search_results"],
        )
    )

    state["agent_outputs"]["analysis"] = result["response"]
    state["active_agent"] = "analysis_agent"
    state["response"] = result["response"]
    state["response_type"] = "analysis"

    duration = (time.time() - start_time) * 1000
    state = update_state_metrics(state, "agent_execution", duration)

    state["messages"].append(AIMessage(content=result["response"]))

    return state


async def recommendation_node(state: AgentState) -> AgentState:
    """推荐Agent节点"""
    start_time = time.time()

    agent = RecommendationAgent()
    result = await agent.execute(
        AgentInput(
            query=state["user_input"],
            tenant_id=state["tenant_id"],
            session_id=state["session_id"],
            search_results=state["search_results"],
        )
    )

    state["agent_outputs"]["recommendation"] = result["response"]
    state["active_agent"] = "recommendation_agent"
    state["response"] = result["response"]
    state["response_type"] = "recommendations"
    state["suggestions"] = result.get("suggestions", [])

    duration = (time.time() - start_time) * 1000
    state = update_state_metrics(state, "agent_execution", duration)

    state["messages"].append(AIMessage(content=result["response"]))

    return state


async def qa_node(state: AgentState) -> AgentState:
    """问答Agent节点"""
    start_time = time.time()

    agent = QAAgent()
    result = await agent.execute(
        AgentInput(
            query=state["user_input"],
            tenant_id=state["tenant_id"],
            session_id=state["session_id"],
            search_results=state["search_results"],
            context=state["retrieval_context"],
        )
    )

    state["agent_outputs"]["qa"] = result["response"]
    state["active_agent"] = "qa_agent"
    state["response"] = result["response"]
    state["response_type"] = "answer"

    duration = (time.time() - start_time) * 1000
    state = update_state_metrics(state, "agent_execution", duration)

    state["messages"].append(AIMessage(content=result["response"]))

    return state


# ============================================================================
# 综合节点
# ============================================================================

async def synthesizer_node(state: AgentState) -> AgentState:
    """
    综合节点
    汇总多个Agent的输出，生成最终响应
    """
    start_time = time.time()

    agent_outputs = state["agent_outputs"]
    search_results = state["search_results"]

    # 如果有多个Agent输出，进行综合
    if len(agent_outputs) > 1:
        # TODO: 使用LLM进行综合
        response = "综合分析:\n\n"
        for agent_name, output in agent_outputs.items():
            response += f"## {agent_name}\n{output}\n\n"
    else:
        response = state.get("response", "抱歉，我无法处理您的请求。")

    state["response"] = response
    state["response_type"] = "synthesized"

    duration = (time.time() - start_time) * 1000
    state = update_state_metrics(state, "synthesis", duration)

    return state


# ============================================================================
# 澄清节点
# ============================================================================

async def clarification_node(state: AgentState) -> AgentState:
    """
    澄清节点
    当意图不明确时，生成澄清问题
    """
    state["requires_clarification"] = True
    state["response_type"] = "clarification_question"
    state["active_agent"] = "qa_agent"

    # 根据输入生成澄清问题
    questions = [
        "您是想搜索CAD模型，还是查找相似的设计？",
        "请提供更多细节，比如具体的参数或应用场景。",
        "您是想了解某个模型的特点，还是需要推荐？",
    ]

    state["suggestions"] = questions
    state["response"] = "我需要更多信息来帮助您。请从以下选项中选择或提供更多细节："

    return state


# ============================================================================
# 错误处理节点
# ============================================================================

async def error_handler_node(state: AgentState) -> AgentState:
    """错误处理节点"""
    error = state.get("error", "Unknown error")

    state["response"] = f"处理请求时发生错误: {error}"
    state["response_type"] = "error"

    state["messages"].append(AIMessage(
        content=f"错误: {error}",
    ))

    return state
