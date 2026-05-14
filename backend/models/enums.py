"""
枚举定义
"""
from enum import Enum


class IntentType(str, Enum):
    """用户意图类型"""
    SEARCH = "search"               # 搜索CAD模型
    SIMILARITY = "similarity"       # 相似度搜索
    ANALYSIS = "analysis"           # 模型分析
    RECOMMENDATION = "recommendation"  # 推荐
    QA = "qa"                       # 问答
    CLARIFICATION = "clarification"  # 澄清需求
    UNKNOWN = "unknown"


class ResponseType(str, Enum):
    """响应类型"""
    ANSWER = "answer"               # 直接回答
    SEARCH_RESULTS = "search_results"  # 搜索结果
    RECOMMENDATIONS = "recommendations"  # 推荐
    CLARIFICATION_QUESTION = "clarification_question"  # 反问
    SYNTHESIZED = "synthesized"     # 综合响应
    ERROR = "error"                 # 错误


class AgentType(str, Enum):
    """Agent类型"""
    SEARCH = "search_agent"
    ANALYSIS = "analysis_agent"
    RECOMMENDATION = "recommendation_agent"
    QA = "qa_agent"
    ORCHESTRATOR = "orchestrator"


class ToolType(str, Enum):
    """工具类型"""
    CAD_SEARCH = "cad_search"
    SIMILARITY_SEARCH = "similarity_search"
    METADATA_QUERY = "metadata_query"
    FILE_ANALYZER = "file_analyzer"
    VECTOR_SEARCH = "vector_search"
    HYBRID_SEARCH = "hybrid_search"


class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
