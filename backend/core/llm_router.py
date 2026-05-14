"""
LLM智能路由
根据任务复杂度自动选择最合适的LLM模型
"""
from typing import List, Dict, Any, Optional
from enum import Enum
import time

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from ..config import settings
from ..models.enums import AgentType


class ModelTier(str, Enum):
    """模型层级"""
    FAST = "fast"           # 快速响应，成本低
    BALANCED = "balanced"   # 平衡性能和成本
    COMPLEX = "complex"     # 复杂推理，质量高


class LLMRouter:
    """
    LLM智能路由器

    根据以下因素选择模型:
    1. 任务复杂度
    2. Agent类型
    3. 输入长度
    4. 成本敏感度

    模型映射:
    - FAST: Claude Haiku / GPT-4o-mini
    - BALANCED: Claude Sonnet / GPT-4o
    - COMPLEX: Claude Opus / GPT-4-turbo
    """

    # 模型配置
    MODELS = {
        ModelTier.FAST: {
            "anthropic": "claude-haiku-4-20250123",
            "openai": "deepseek-v4-flash",
        },
        ModelTier.BALANCED: {
            "anthropic": "claude-sonnet-4-20250514",
            "openai": "deepseek-v4-flash",
        },
        ModelTier.COMPLEX: {
            "anthropic": "claude-opus-4-20250514",
            "openai": "deepseek-v4-flash",
        },
    }

    # 定价 (USD/1M tokens)
    PRICING = {
        "claude-haiku-4-20250123": {"input": 0.25, "output": 1.25},
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    }

    def __init__(self):
        # 优先使用配置好 API Key 的提供商
        if settings.ANTHROPIC_API_KEY:
            self.provider = "anthropic"
        else:
            self.provider = "openai"
        self.cost_sensitivity = settings.LLM_ROUTING.get("cost_sensitivity", "balanced") if hasattr(settings, 'LLM_ROUTING') else "balanced"

    async def get_llm(
        self,
        agent_type: AgentType,
        messages: List[BaseMessage],
    ) -> BaseChatModel:
        """
        根据Agent类型和消息内容选择合适的LLM

        Args:
            agent_type: Agent类型
            messages: 消息列表

        Returns:
            LLM实例
        """
        # 分析任务复杂度
        tier = self._analyze_complexity(agent_type, messages)

        # 获取模型名称
        model_name = self._get_model_name(tier)

        # 创建LLM实例
        return self._create_llm(model_name)

    def get_model_by_name(self, model_name: str) -> BaseChatModel:
        """根据名称创建LLM实例"""
        return self._create_llm(model_name)

    def _analyze_complexity(
        self,
        agent_type: AgentType,
        messages: List[BaseMessage],
    ) -> ModelTier:
        """
        分析任务复杂度

        规则:
        1. QA Agent -> FAST (快速响应)
        2. Search Agent -> BALANCED (需要理解查询)
        3. Analysis Agent -> COMPLEX (需要深度分析)
        4. Recommendation Agent -> BALANCED (需要权衡)
        5. 长文本输入 -> COMPLEX (需要更多上下文处理)
        """
        # 计算输入长度
        total_chars = sum(len(m.content) for m in messages)

        # 基于Agent类型
        if agent_type == AgentType.QA:
            base_tier = ModelTier.FAST
        elif agent_type == AgentType.ANALYSIS:
            base_tier = ModelTier.COMPLEX
        elif agent_type == AgentType.SEARCH:
            base_tier = ModelTier.BALANCED
        elif agent_type == AgentType.RECOMMENDATION:
            base_tier = ModelTier.BALANCED
        else:
            base_tier = ModelTier.BALANCED

        # 根据输入长度调整
        if total_chars > 10000:  # 长文本
            if base_tier == ModelTier.FAST:
                base_tier = ModelTier.BALANCED
            else:
                base_tier = ModelTier.COMPLEX

        # 根据成本敏感度调整
        if self.cost_sensitivity == "high":
            # 优先使用更便宜的模型
            if base_tier == ModelTier.COMPLEX:
                base_tier = ModelTier.BALANCED
            elif base_tier == ModelTier.BALANCED:
                base_tier = ModelTier.FAST

        return base_tier

    def _get_model_name(self, tier: ModelTier) -> str:
        """获取模型名称"""
        return self.MODELS[tier][self.provider]

    def _create_llm(self, model_name: str) -> BaseChatModel:
        """创建LLM实例"""
        if "claude" in model_name.lower():
            return ChatAnthropic(
                model=model_name,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.7,
                max_tokens=2048,
            )
        else:
            return ChatOpenAI(
                model=model_name,
                openai_api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                temperature=0.7,
                max_tokens=2048,
            )

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        计算LLM调用成本

        Args:
            model: 模型名称
            prompt_tokens: 输入token数
            completion_tokens: 输出token数

        Returns:
            成本（USD）
        """
        if model not in self.PRICING:
            return 0.0

        pricing = self.PRICING[model]
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost


# ============================================================================
# 全局实例
# ============================================================================

_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """获取LLM路由器单例"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
