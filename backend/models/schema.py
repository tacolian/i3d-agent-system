"""
数据模型定义
使用Pydantic v2
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from .enums import IntentType, ResponseType, AgentType, ToolType, MessageRole, TaskStatus


# ============================================================================
# 请求模型
# ============================================================================

class TenantContext(BaseModel):
    """租户上下文"""
    tenant_id: str = Field(..., description="租户ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    request_id: Optional[str] = Field(None, description="请求ID")

    @field_validator("tenant_id")
    def validate_tenant(cls, v):
        from ..config import settings, TenantConfig
        if not TenantConfig.is_valid_tenant(v):
            raise ValueError(f"Invalid tenant_id: {v}")
        return v


class Message(BaseModel):
    """聊天消息"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_calls: Optional[List["ToolCall"]] = None


class ChatRequest(BaseModel):
    """聊天请求"""
    query: str = Field(..., min_length=1, max_length=2000, description="用户查询")
    session_id: Optional[str] = Field(None, description="会话ID")
    tenant_context: TenantContext = Field(..., description="租户上下文")
    stream: bool = Field(True, description="是否流式响应")
    intent: Optional[IntentType] = Field(None, description="指定意图（可选）")
    max_results: int = Field(10, ge=1, le=50, description="最大结果数")
    enable_rag: bool = Field(True, description="启用RAG检索")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="生成温度")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    tenant_id: str = Field(..., description="租户ID")
    file_name: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    chunk_size: int = Field(512, ge=100, le=2000, description="分块大小")
    chunk_overlap: int = Field(50, ge=0, le=200, description="分块重叠")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")


# ============================================================================
# 响应模型
# ============================================================================

class ToolCall(BaseModel):
    """工具调用记录"""
    tool_name: ToolType
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class LatencyMetrics(BaseModel):
    """延迟指标"""
    total_ms: float
    intent_classification_ms: float = 0.0
    routing_ms: float = 0.0
    retrieval_ms: float = 0.0
    generation_ms: float = 0.0
    tool_calls_ms: float = 0.0


class LLMCall(BaseModel):
    """LLM调用记录"""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float


class AgentResponse(BaseModel):
    """Agent响应"""
    response: str = Field(..., description="响应内容")
    response_type: ResponseType = Field(..., description="响应类型")
    intent: IntentType = Field(..., description="识别的意图")
    intent_confidence: float = Field(..., ge=0.0, le=1.0, description="意图置信度")
    agent_used: AgentType = Field(..., description="使用的Agent")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="工具调用记录")
    search_results: Optional[List["SearchResult"]] = Field(None, description="搜索结果")
    llm_calls: List[LLMCall] = Field(default_factory=list, description="LLM调用记录")
    latency: LatencyMetrics = Field(..., description="延迟指标")
    session_id: str = Field(..., description="会话ID")
    requires_clarification: bool = Field(False, description="是否需要澄清")
    suggestions: Optional[List[str]] = Field(None, description="建议列表")


class StreamChunk(BaseModel):
    """流式响应块"""
    chunk_type: Literal["content", "tool_call", "metadata", "error"]
    content: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    is_final: bool = False


class ChatResponse(BaseModel):
    """聊天响应（非流式）"""
    request_id: str
    session_id: str
    response: AgentResponse
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# 内部模型
# ============================================================================

class SearchParams(BaseModel):
    """搜索参数"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 10
    similarity_threshold: float = 0.7
    search_type: Literal["vector", "hybrid", "metadata"] = "hybrid"


class SearchResult(BaseModel):
    """搜索结果"""
    item_code: str
    file_name: str
    file_path: str
    similarity: float
    metadata: Dict[str, Any]
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None


class DocumentChunk(BaseModel):
    """文档分块"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: Optional[float] = None


class AgentState(BaseModel):
    """Agent状态（用于LangGraph）"""
    # 输入
    user_input: str
    tenant_id: str
    session_id: str
    request_id: str
    max_results: int

    # 中间状态
    intent: IntentType = IntentType.UNKNOWN
    intent_confidence: float = 0.0
    search_params: Optional[SearchParams] = None
    search_results: List[SearchResult] = Field(default_factory=list)

    # 输出
    agent_response: str = ""
    response_type: ResponseType = ResponseType.ANSWER
    tool_calls: List[ToolCall] = Field(default_factory=list)
    intermediate_steps: List[Dict[str, Any]] = Field(default_factory=list)

    # 指标
    latency: Dict[str, float] = Field(default_factory=dict)
    llm_calls: List[LLMCall] = Field(default_factory=list)

    # 控制流
    next_action: Optional[str] = None
    requires_clarification: bool = False
    error: Optional[str] = None


# ============================================================================
# 健康检查模型
# ============================================================================

class HealthCheck(BaseModel):
    """健康检查响应"""
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, Literal["healthy", "unhealthy"]]
