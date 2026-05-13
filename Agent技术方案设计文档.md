# 3D CAD 智能检索系统 - Agent 技术方案设计文档

> **文档版本**: v1.0
> **创建日期**: 2026-05-13
> **项目名称**: 基于 Multi-Agent 的 3D CAD 智能检索与处理平台

---

## 目录

1. [项目概述](#1-项目概述)
2. [2026年主流 Agent 技术调研](#2-2026年主流-agent-技术调研)
3. [技术选型与架构设计](#3-技术选型与架构设计)
4. [详细实施方案](#4-详细实施方案)
5. [技术实现细节](#5-技术实现细节)
6. [部署与运维](#6-部署与运维)
7. [风险评估与应对](#7-风险评估与应对)
8. [实施计划](#8-实施计划)

---

## 1. 项目概述

### 1.1 项目背景

当前 3D CAD 智能检索与处理系统基于 Django + PostgreSQL + pgvector 架构，已实现基础的向量检索功能。为提升用户体验、降低使用门槛，计划引入 AI Agent 技术，实现自然语言交互、智能推荐、自动化分析等高级功能。

### 1.2 项目目标

| 目标 | 当前状态 | 目标状态 | 提升幅度 |
|------|----------|----------|----------|
| 检索准确率 | 基准 | +40% | 基于评估集 |
| 用户查询耗时 | 平均 3 次交互 | 1 次交互 | -66% |
| 并发支持 | 现有水平 | 200 QPS | +100% |
| 响应时间 (P95) | - | < 2s | 新增指标 |
| Token 成本 | - | 优化后降低 50% | 成本控制 |

### 1.3 核心价值

- **用户体验**: 自然语言查询，无需学习专业检索语法
- **效率提升**: 多 Agent 协作，一次查询完成复杂任务
- **智能推荐**: 基于上下文和历史的个性化推荐
- **自动化分析**: CAD 模型自动标注、质量检测

---

## 2. 2026年主流 Agent 技术调研

### 2.1 国际主流框架对比

| 框架 | 厂商 | 状态 | 生产就绪度 | 核心特点 | 适用场景 |
|------|------|------|------------|----------|----------|
| **Microsoft Agent Framework** | Microsoft | GA (2026.04) | ⭐⭐⭐⭐⭐ | Semantic Kernel + AutoGen 合并，企业级特性 | 企业级应用，.NET/Python |
| **LangGraph** | LangChain | 成熟 | ⭐⭐⭐⭐⭐ | 图编排，状态管理，LangSmith 集成 | 复杂 Agent 编排 |
| **OpenAI Swarm** | OpenAI | 轻量级 | ⭐⭐⭐⭐ | 轻量级，教育友好 | 快速原型，简单编排 |
| **CrewAI** | 开源 | 活跃 | ⭐⭐⭐⭐ | Python 原生，角色定义清晰 | 多角色协作 |
| **Anthropic Tool Use** | Anthropic | 成熟 | ⭐⭐⭐⭐⭐ | MCP 协议，Computer Use | Claude 集成 |

### 2.2 技术趋势分析（2026）

根据 [LangChain State of Agent Engineering Report 2026](https://www.langchain.com/state-of-agent-engineering)：

1. **从"是否构建"到"如何部署"**: 企业已越过 Agent 可行性验证阶段，关注生产部署
2. **状态管理是核心痛点**: 60% 的生产事故与状态管理相关
3. **多 Agent 协作成熟**: 从单 Agent 向多 Agent 协作演进
4. **可观测性成为刚需**: Agent 决策链追踪、调试、监控
5. **成本优化**: 智能路由、缓存、批处理成为标配

### 2.3 国内大厂实践

| 厂商 | Agent 方案 | 特点 |
|------|-----------|------|
| **字节跳动** | 豆包 Agent | 多模态理解，工具调用 |
| **阿里巴巴** | 通义千问 Agent | 企业知识库集成，RAG |
| **百度** | 文心智能体 | 零代码构建，可视化编排 |
| **腾讯** | 混元 Agent | 多 Agent 协作，企业级部署 |

---

## 3. 技术选型与架构设计

### 3.1 技术选型

#### 3.1.1 核心框架选择: **LangGraph**

**选择理由**:

| 维度 | LangGraph | 其他方案 |
|------|-----------|----------|
| 生产成熟度 | 2026年事实标准 | Microsoft AF 较新，Swarm 过于轻量 |
| 状态管理 | 内置 Checkpointing，支持持久化 | 需自行实现 |
| 可观测性 | LangSmith 原生集成 | 需额外集成 |
| 社区生态 | 最活跃 (30K+ GitHub Stars) | 相对较小 |
| Python 原生 | 完全支持 | Microsoft AF 偏向 .NET |

#### 3.1.2 LLM 选择策略

```
┌─────────────────────────────────────────────────────────────┐
│                    智能 LLM 路由                            │
├─────────────────────────────────────────────────────────────┤
│  任务类型                  │  推荐模型        │  成本      │
├─────────────────────────────────────────────────────────────┤
│  意图识别/参数提取        │  Claude Haiku   │  低        │
│  复杂推理/多轮对话        │  Claude Sonnet  │  中        │
│  代码生成/数据分析        │  Claude Opus    │  高        │
│  简单问答                 │  本地 BGE M3    │  免费      │
└─────────────────────────────────────────────────────────────┘
```

#### 3.1.3 技术栈全景

```
┌───────────────────────────────────────────────────────────────┐
│                         前端层                                │
│  Vue 3 + WebSocket + Three.js (3D 预览)                      │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                    Agent 服务层 (新增)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ LangGraph    │  │ FastAPI      │  │ Celery       │        │
│  │ Agent 编排   │  │ REST/WebSocket│  │ 异步任务     │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                      AI 能力层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │Claude API│  │BGE M3    │  │CLIP     │  │本地 Embed │     │
│  │推理      │  │本地向量  │  │图像理解  │  │ding      │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                    数据与存储层 (复用)                         │
│  PostgreSQL + pgvector  │  Redis  │  MinIO  │  RabbitMQ    │
└───────────────────────────────────────────────────────────────┘
                              │
┌───────────────────────────────────────────────────────────────┐
│                    监控与可观测性 (新增)                       │
│  LangSmith  │  Prometheus  │  Grafana  │  自研 Tracer     │
└───────────────────────────────────────────────────────────────┘
```

### 3.2 系统架构设计

#### 3.2.1 整体架构图

```
                    用户 (3d-desktopprogram)
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Gateway Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 请求路由      │  │ 认证鉴权      │  │ 租户隔离      │          │
│  │ (Router)     │  │ (Auth)       │  │ (Tenant)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
┌───────────────▼──────┐ ┌────▼─────────┐ ┌──▼──────────────────┐
│  检索 Agent           │ │ 分析 Agent    │ │ 推荐 Agent          │
│  - 意图识别           │ │ - CAD 分析    │ │ - 个性化推荐        │
│  - 查询改写           │ │ - 特征提取    │ │ - 协同过滤          │
│  - 结果整合           │ │ - 工艺识别    │ │ - 冷启动处理        │
└───────────┬───────────┘ └────┬─────────┘ └──┬──────────────────┘
            │                   │               │
            └───────────────────┼───────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      Tool Layer (工具层)                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │向量检索Tool│ │元数据查询  │ │模型分析Tool│ │RAG检索Tool │   │
│  │(pgvector) │ │(PostgreSQL)│ │(CAD解析)   │ │(Hybrid)    │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
└───────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      现有服务层 (复用)                           │
│  InferEngineer-3dRetrieval │ 3d-search-core │ xxl_job_executor │
└───────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 Agent 编排架构

```
┌───────────────────────────────────────────────────────────────────┐
│                    LangGraph State Machine                        │
│                                                                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│  │  Start  │───▶│ Intent  │───▶│ Router  │───▶│ Agent   │       │
│  │  State  │    │ Analysis│    │  Logic  │    │ Dispatch│       │
│  └─────────┘    └─────────┘    └─────────┘    └────┬────┘       │
│                                                  │             │
│        ┌─────────────────────────────────────────┼─────────────┤│
│        ▼                                         ▼             ▼│
│  ┌───────────┐    ┌───────────┐    ┌───────────┐  ┌─────────┐ ││
│  │  Search   │    │  Analyze  │    │ Recommend │  │  QA     │ ││
│  │  Agent    │    │  Agent    │    │  Agent    │  │  Agent  │ ││
│  └─────┬─────┘    └─────┬─────┘    └─────┬─────┘  └────┬────┘ ││
│        │                │                │             │      ││
│        └────────────────┼────────────────┼─────────────┘      ││
│                         ▼                ▼                      ││
│                   ┌─────────────┐  ┌─────────────┐             ││
│                   │ Tool Calls  │  │ Result      │             ││
│                   │ (Parallel)  │  │ Aggregation │             ││
│                   └──────┬──────┘  └──────┬──────┘             ││
│                          │                │                     ││
│                          ▼                ▼                     ││
│                   ┌─────────────────────────────┐               ││
│                   │      Response Generation    │               ││
│                   │      (LLM + Templates)      │               ││
│                   └─────────────┬───────────────┘               ││
│                                 ▼                               ││
│                           ┌───────────┐                          ││
│                           │   End     │                          ││
│                           │  State    │                          ││
│                           └───────────┘                          ││
└───────────────────────────────────────────────────────────────────┘
```

---

## 4. 详细实施方案

### 4.1 Agent 定义

#### 4.1.1 检索 Agent (Search Agent)

**职责**: 处理用户检索请求，将自然语言转换为结构化查询

**核心能力**:
```python
# 意图识别
意图类型 = [
    "semantic_search",      # 语义搜索: "找类似法兰盘的零件"
    "filtered_search",      # 过滤搜索: "直径小于200mm的螺栓"
    "similarity_search",    # 相似度搜索: "和这个模型像的"
    "attribute_query",      # 属性查询: "这个零件的材料是什么"
]

# 查询改写
原始: "法兰盖" → 改写: "法兰盘" (同义词扩展)
原始: "找个螺丝" → 改写: "螺栓" (标准化)

# 参数提取
"找直径不超过200mm的法兰盘" → {
    "query": "法兰盘",
    "filters": {"diameter": {"$lte": 200}}
}
```

#### 4.1.2 分析 Agent (Analysis Agent)

**职责**: 分析 CAD 模型，提取特征和元数据

**核心能力**:
```python
分析维度 = {
    "几何特征": ["体积", "表面积", "孔洞数量", "壁厚"],
    "拓扑特征": ["面数量", "边数量", "顶点数量", "连通性"],
    "工艺特征": ["钣金件", "铸造件", "机加工件", "注塑件"],
    "质量检测": ["非流形边", "重复面", "退化面", "自相交"]
}
```

#### 4.1.3 推荐 Agent (Recommendation Agent)

**职责**: 基于上下文和历史提供个性化推荐

**核心能力**:
```python
推荐策略 = {
    "协同过滤": "看过这个的人也看过",
    "内容相似": "几何特征相似的模型",
    "时序推荐": "最近上传的相关模型",
    "冷启动": "基于热门度/质量分"
}
```

#### 4.1.4 问答 Agent (QA Agent)

**职责**: 回答关于 CAD 设计、工艺、材料的问题

**核心能力**:
```python
知识领域 = {
    "设计规范": "GB/T、ISO 标准解读",
    "加工工艺": "钣金/铸造/机加工工艺参数",
    "材料选择": "常用材料特性与适用场景",
    "成本估算": "基于特征的成本预估"
}
```

### 4.2 Tool 设计

#### 4.2.1 向量检索 Tool

```python
@tool
def vector_search(
    query: str,
    filters: dict = None,
    top_k: int = 10,
    tenant_id: str = None
) -> List[Dict]:
    """
    执行向量检索，支持语义搜索和过滤

    Args:
        query: 查询文本
        filters: 元数据过滤条件
        top_k: 返回结果数量
        tenant_id: 租户ID

    Returns:
        检索结果列表，包含相似度分数和元数据
    """
    # 调用现有 pgvector API
    response = requests.post(
        "http://localhost:18000/api/search/semanticSearch",
        json={
            "query_text": query,
            "filters": filters or {},
            "page_size": top_k,
            "tenant_id": tenant_id
        }
    )
    return response.json()
```

#### 4.2.2 混合检索 Tool

```python
@tool
def hybrid_search(
    query: str,
    alpha: float = 0.7,  # 语义权重
    filters: dict = None,
    top_k: int = 10
) -> List[Dict]:
    """
    混合检索：BM25 + 向量检索

    Args:
        query: 查询文本
        alpha: 语义检索权重 (0-1)，1-alpha 为 BM25 权重
        filters: 元数据过滤条件
        top_k: 返回结果数量

    Returns:
        融合后的检索结果
    """
    # 并行执行 BM25 和向量检索
    bm25_results = bm25_search(query, filters, top_k * 2)
    vector_results = vector_search(query, filters, top_k * 2)

    # RRF (Reciprocal Rank Fusion) 融合
    return rrf_fusion(bm25_results, vector_results, alpha, top_k)
```

#### 4.2.3 CAD 分析 Tool

```python
@tool
def analyze_cad_model(
    file_path: str,
    analysis_type: List[str] = None
) -> Dict:
    """
    分析 CAD 模型特征

    Args:
        file_path: CAD 文件路径
        analysis_type: 分析类型列表
                       ["geometry", "topology", "quality", "process"]

    Returns:
        分析结果字典
    """
    # 调用 3d-search-core 的分析接口
    response = requests.post(
        "http://localhost:28000/api/analysis/extract_features",
        json={
            "file_path": file_path,
            "analysis_types": analysis_type or ["geometry", "quality"]
        }
    )
    return response.json()
```

#### 4.2.4 RAG 检索 Tool

```python
@tool
def rag_search(
    query: str,
    context_type: str = "knowledge_base",
    top_k: int = 5
) -> List[Dict]:
    """
    从知识库检索相关文档

    Args:
        query: 查询文本
        context_type: 上下文类型
                      ["knowledge_base", "design_spec", "process_guide"]
        top_k: 返回文档数量

    Returns:
        相关文档片段
    """
    # 从文档向量库检索
    response = requests.post(
        f"{RAG_SERVICE_URL}/api/retrieve",
        json={
            "query": query,
            "collection": context_type,
            "top_k": top_k
        }
    )
    return response.json()
```

### 4.3 RAG 系统设计

#### 4.3.1 文档处理 Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      文档摄取 Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  原始文档 (CAD 规范/设计手册/工艺指南)                            │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────┐                                                │
│  │ 文档解析    │  → 提取文本、表格、图片                         │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ 智能切片    │  → 语义切分 (保持上下文完整性)                   │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ Embedding   │  → BGE M3 生成向量                             │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ 元数据提取  │  → LLM 提取标题、摘要、关键词                     │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ 写入向量库  │  → pgvector 存储                                │
│  └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.3.2 切片策略对比

| 策略 | 实现 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|----------|
| **固定长度** | 按字符数切分 | 简单高效 | 可能截断语义 | 结构化文档 |
| **语义切分** | 按段落/章节切分 | 保持语义完整 | 需要解析结构 | 技术文档 |
| **递归切分** | 多级切分 | 兼顾粒度 | 复杂度高 | 长文档 |
| **LLM 辅助** | 智能判断切分点 | 最准确 | 成本高 | 高价值文档 |

**推荐方案**: 语义切分 + LLM 辅助 (混合方案)

#### 4.3.3 检索增强策略

```python
# 查询扩展
def query_expansion(original_query: str) -> List[str]:
    """生成同义词和相关查询"""
    expanded = llm.invoke(
        f"""为以下查询生成 3 个同义或相关的查询:
        原查询: {original_query}

        输出格式: JSON 数组
        """
    )
    return expanded + [original_query]

# HyDE (Hypothetical Document Embeddings)
def hyde_search(query: str) -> str:
    """生成假设文档后再检索"""
    hypothetical_doc = llm.invoke(
        f"""基于查询生成一个假设的答案文档:
        查询: {query}
        """
    )
    # 用假设文档的向量进行检索
    return vector_search(hypothetical_doc)

# 重排序
def rerank(initial_results: List[Dict], query: str) -> List[Dict]:
    """使用 Cross-Encoder 重排序"""
    scores = cross_encoder.predict(
        [[query, doc["text"]] for doc in initial_results]
    )
    # 按重排序分数重新排列
    return sorted(initial_results, key=lambda x: scores, reverse=True)
```

---

## 5. 技术实现细节

### 5.1 LangGraph Agent 实现

#### 5.1.1 状态定义

```python
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    """Agent 状态定义"""
    # 用户输入
    user_input: str
    tenant_id: Optional[str]
    session_id: str

    # 意图识别
    intent: str
    intent_confidence: float

    # 查询参数
    search_params: dict

    # 检索结果
    search_results: List[Dict]

    # Agent 输出
    agent_response: str
    response_type: str  # "search_result", "recommendation", "analysis", "qa"

    # 中间步骤（用于可观测性）
    intermediate_steps: List[dict]
    tool_calls: List[dict]

    # 元数据
    latency: dict
    llm_calls: List[dict]
```

#### 5.1.2 节点定义

```python
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# 意图识别节点
async def intent_node(state: AgentState) -> AgentState:
    """识别用户意图"""
    prompt = f"""分析用户查询意图，从以下选项中选择:
    - semantic_search: 语义搜索
    - filtered_search: 带过滤条件的搜索
    - similarity_search: 与特定模型相似的搜索
    - attribute_query: 属性查询
    - recommendation: 请求推荐
    - analysis: 模型分析
    - qa: 知识问答

    用户查询: {state['user_input']}

    返回 JSON: {{"intent": "xxx", "confidence": 0.9}}
    """

    response = await llm_with_structured_output.ainvoke(prompt)
    state["intent"] = response["intent"]
    state["intent_confidence"] = response["confidence"]
    state["intermediate_steps"].append({"intent": response})
    return state

# 路由节点
def router_node(state: AgentState) -> str:
    """根据意图路由到不同 Agent"""
    intent = state["intent"]

    routing = {
        "semantic_search": "search_agent",
        "filtered_search": "search_agent",
        "similarity_search": "search_agent",
        "attribute_query": "search_agent",
        "recommendation": "recommend_agent",
        "analysis": "analysis_agent",
        "qa": "qa_agent"
    }

    return routing.get(intent, "search_agent")

# 搜索 Agent 节点
async def search_agent_node(state: AgentState) -> AgentState:
    """执行搜索任务"""
    # 构建搜索参数
    search_params = await build_search_params(state)

    # 调用检索 Tool
    results = await vector_search(
        query=search_params["query"],
        filters=search_params.get("filters"),
        top_k=search_params.get("top_k", 10),
        tenant_id=state.get("tenant_id")
    )

    state["search_results"] = results
    state["tool_calls"].append({"tool": "vector_search", "params": search_params})

    # 生成自然语言响应
    response = await generate_search_response(results, state["user_input"])
    state["agent_response"] = response
    state["response_type"] = "search_result"

    return state

# 响应生成节点
async def response_generator_node(state: AgentState) -> AgentState:
    """生成最终响应"""
    # 如果已有响应，直接返回
    if state.get("agent_response"):
        return state

    # 默认响应
    state["agent_response"] = "抱歉，我无法理解您的请求。"
    return state
```

#### 5.1.3 图构建

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

# 创建图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("intent", intent_node)
workflow.add_node("router", router_node)
workflow.add_node("search_agent", search_agent_node)
workflow.add_node("analysis_agent", analysis_agent_node)
workflow.add_node("recommend_agent", recommend_agent_node)
workflow.add_node("qa_agent", qa_agent_node)
workflow.add_node("response", response_generator_node)

# 设置入口
workflow.set_entry_point("intent")

# 添加边
workflow.add_conditional_edges(
    "intent",
    router_node,
    {
        "search_agent": "search_agent",
        "analysis_agent": "analysis_agent",
        "recommend_agent": "recommend_agent",
        "qa_agent": "qa_agent"
    }
)

# Agent 节点都连接到响应节点
workflow.add_edge("search_agent", "response")
workflow.add_edge("analysis_agent", "response")
workflow.add_edge("recommend_agent", "response")
workflow.add_edge("qa_agent", "response")

# 响应节点结束
workflow.add_edge("response", END)

# 添加持久化（状态管理）
checkpoint_saver = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:15433/i3d_multitenant"
)

# 编译图
app = workflow.compile(checkpointer=checkpoint_saver)
```

### 5.2 FastAPI 服务实现

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="I3D Agent Service", version="1.0.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class ChatRequest(BaseModel):
    message: str
    session_id: str
    tenant_id: Optional[str] = None
    stream: bool = False

# 响应模型
class ChatResponse(BaseModel):
    reply: str
    session_id: str
    agent_type: str
    metadata: dict

# POST 接口
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """处理聊天请求"""
    try:
        # 初始化状态
        config = {
            "configurable": {
                "thread_id": request.session_id,
                "tenant_id": request.tenant_id
            }
        }

        # 调用 Agent
        result = await app.ainvoke(
            {
                "user_input": request.message,
                "tenant_id": request.tenant_id,
                "session_id": request.session_id,
                "intermediate_steps": [],
                "tool_calls": [],
                "llm_calls": []
            },
            config=config
        )

        return ChatResponse(
            reply=result["agent_response"],
            session_id=request.session_id,
            agent_type=result.get("response_type", "unknown"),
            metadata={
                "intent": result.get("intent"),
                "tool_calls": result.get("tool_calls", []),
                "latency": result.get("latency", {})
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket 流式接口
@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """WebSocket 流式聊天"""
    await websocket.accept()

    try:
        # 接收初始消息
        data = await websocket.receive_json()
        session_id = data.get("session_id")
        tenant_id = data.get("tenant_id")

        config = {
            "configurable": {
                "thread_id": session_id,
                "tenant_id": tenant_id
            }
        }

        # 流式调用 Agent
        async for chunk in app.astream(
            {
                "user_input": data.get("message"),
                "tenant_id": tenant_id,
                "session_id": session_id
            },
            config=config,
            stream_mode="updates"
        ):
            # 发送增量更新
            await websocket.send_json({
                "type": "update",
                "data": chunk
            })

        # 发送最终响应
        await websocket.send_json({
            "type": "done",
            "data": result
        })

    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
```

### 5.3 智能 LLM 路由

```python
from enum import Enum
from typing import Literal

class TaskComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

class LLMRouter:
    """智能 LLM 路由器"""

    def __init__(self):
        self.models = {
            "haiku": {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 8192,
                "cost_per_1k_tokens": 0.0008
            },
            "sonnet": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.003
            },
            "opus": {
                "model": "claude-3-5-opus-20241022",
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.015
            }
        }

    async def classify_task(self, query: str, context: dict) -> TaskComplexity:
        """分类任务复杂度"""
        # 简单规则分类
        if len(query) < 50 and not any(keyword in query for keyword in
            ["分析", "推荐", "比较", "为什么", "如何"]):
            return TaskComplexity.SIMPLE

        if any(keyword in query for keyword in
            ["详细分析", "深入", "多角度", "综合"]):
            return TaskComplexity.COMPLEX

        return TaskComplexity.MEDIUM

    async def route(self, query: str, context: dict) -> str:
        """路由到合适的模型"""
        complexity = await self.classify_task(query, context)

        routing = {
            TaskComplexity.SIMPLE: "haiku",
            TaskComplexity.MEDIUM: "sonnet",
            TaskComplexity.COMPLEX: "opus"
        }

        # 检查是否有特定需求
        if context.get("requires_code_generation"):
            return "opus"
        if context.get("requires_fast_response"):
            return "haiku"

        model_name = routing[complexity]
        return self.models[model_name]["model"]

# 使用示例
router = LLMRouter()

async def process_query(query: str, context: dict):
    # 路由到合适的模型
    model = await router.route(query, context)

    # 调用 LLM
    response = await anthropic_client.messages.create(
        model=model,
        messages=[{"role": "user", "content": query}]
    )

    return response
```

### 5.4 可观测性实现

```python
from langsmith import traceable
import time
from typing import Dict, Any
import json

class AgentObservability:
    """Agent 可观测性管理"""

    def __init__(self):
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.prometheus_host = os.getenv("PROMETHEUS_HOST")

    @traceable(name="agent_execution")
    async def trace_agent_execution(
        self,
        state: AgentState,
        node_name: str,
        node_function
    ) -> Dict[str, Any]:
        """追踪 Agent 执行"""
        start_time = time.time()

        # 记录输入
        input_data = {
            "node": node_name,
            "state_keys": list(state.keys()),
            "user_input": state.get("user_input", "")[:100]
        }

        try:
            # 执行节点函数
            result = await node_function(state)

            # 记录输出
            output_data = {
                "node": node_name,
                "duration_ms": (time.time() - start_time) * 1000,
                "success": True,
                "output_keys": list(result.keys()) if isinstance(result, dict) else []
            }

            # 记录 LLM 调用
            if "llm_calls" in result:
                for call in result["llm_calls"]:
                    self.record_llm_call(call)

            return result

        except Exception as e:
            # 记录错误
            output_data = {
                "node": node_name,
                "duration_ms": (time.time() - start_time) * 1000,
                "success": False,
                "error": str(e)
            }
            raise

    def record_llm_call(self, call_data: dict):
        """记录 LLM 调用"""
        metrics = {
            "model": call_data.get("model"),
            "prompt_tokens": call_data.get("prompt_tokens", 0),
            "completion_tokens": call_data.get("completion_tokens", 0),
            "total_tokens": call_data.get("total_tokens", 0),
            "latency_ms": call_data.get("latency_ms", 0),
            "timestamp": time.time()
        }

        # 发送到 Prometheus
        self.send_to_prometheus(metrics)

    def send_to_prometheus(self, metrics: dict):
        """发送指标到 Prometheus"""
        # 实现指标推送
        pass

# LangSmith 集成示例
from langchain_anthropic import ChatAnthropic
from langchain.callbacks.tracers import LangChainTracer

# 初始化 LangSmith
tracer = LangChainTracer(
    project_name="i3d-agent-production"
)

# 创建带追踪的 LLM
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    callbacks=[tracer],
    metadata={"project": "i3d-cad-search"}
)
```

---

## 6. 部署与运维

### 6.1 Docker 部署

#### 6.1.1 Dockerfile

```dockerfile
# agent-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
```

#### 6.1.2 Docker Compose

```yaml
# docker-compose.agent.yml
version: '3.8'

services:
  agent-service:
    build: ./agent-service
    container_name: i3d-agent-service
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://app_user:password@localhost:15433/i3d_multitenant
      - REDIS_URL=redis://localhost:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./agent-service:/app
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - i3d-network

  redis:
    image: redis:7-alpine
    container_name: i3d-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - i3d-network

  prometheus:
    image: prom/prometheus:latest
    container_name: i3d-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - i3d-network

  grafana:
    image: grafana/grafana:latest
    container_name: i3d-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - grafana-data:/var/lib/grafana
    networks:
      - i3d-network

volumes:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  i3d-network:
    external: true
```

### 6.2 监控配置

#### 6.2.1 Prometheus 配置

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agent-service'
    static_configs:
      - targets: ['agent-service:5000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
```

#### 6.2.2 Grafana Dashboard

监控指标：

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| `agent_request_duration_seconds` | 请求响应时间 | P95 > 2s |
| `agent_requests_total` | 请求总数 | - |
| `agent_errors_total` | 错误总数 | 错误率 > 5% |
| `llm_tokens_used_total` | LLM Token 消耗 | - |
| `llm_cost_total` | LLM 成本 | 每日预算超限 |
| `vector_search_duration_seconds` | 向量检索耗时 | P95 > 500ms |
| `rag_cache_hit_rate` | RAG 缓存命中率 | < 70% |

### 6.3 日志管理

```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """结构化日志格式化"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # 添加自定义字段
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, "agent_type"):
            log_data["agent_type"] = record.agent_type

        # 异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("/app/logs/agent.log"),
        logging.StreamHandler()
    ]
)

for handler in logging.root.handlers:
    handler.setFormatter(JSONFormatter())
```

---

## 7. 风险评估与应对

### 7.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| LLM 幻觉 | 高 | 中 | RAG 约束 + 事实核查 + 人工审核 |
| 响应延迟 | 中 | 中 | 流式输出 + 缓存 + 异步处理 |
| 成本超支 | 中 | 高 | 智能路由 + Token 优化 + 本地模型 |
| 状态管理复杂 | 高 | 高 | LangGraph Checkpointing |
| 多租户隔离 | 高 | 低 | 租户 ID 验证 + RLS |

### 7.2 业务风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| 用户接受度 | 高 | 中 | 渐进式发布 + 反馈收集 |
| 准确率不达标 | 高 | 中 | A/B 测试 + 持续优化 |
| 数据安全 | 高 | 低 | 加密 + 访问控制 + 审计 |

---

## 8. 实施计划

### 8.1 时间规划（16 周）

```
┌─────────────────────────────────────────────────────────────────┐
│                        项目时间表                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: RAG 系统搭建 (Week 1-3)                               │
│  ├─ Week 1:  文档处理 Pipeline                                  │
│  ├─ Week 2:  向量库搭建 + Embedding                             │
│  └─ Week 3:  混合检索 + 重排序                                   │
│                                                                  │
│  Phase 2: Agent 开发 (Week 4-7)                                 │
│  ├─ Week 4:  检索 Agent                                         │
│  ├─ Week 5:  分析 Agent                                         │
│  ├─ Week 6:  推荐 Agent                                         │
│  └─ Week 7:  问答 Agent                                         │
│                                                                  │
│  Phase 3: 编排与集成 (Week 8-10)                                │
│  ├─ Week 8:  LangGraph 编排                                     │
│  ├─ Week 9:  Tool 开发与集成                                    │
│  └─ Week 10: 状态管理 + Checkpointing                           │
│                                                                  │
│  Phase 4: 工程化 (Week 11-13)                                   │
│  ├─ Week 11: 性能优化 + 缓存                                     │
│  ├─ Week 12: 可观测性 + 监控                                     │
│  └─ Week 13: 测试 + 文档                                         │
│                                                                  │
│  Phase 5: 部署与优化 (Week 14-16)                               │
│  ├─ Week 14: Docker 部署                                        │
│  ├─ Week 15: 前端集成                                           │
│  └─ Week 16: 上线 + 优化                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 里程碑

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| M1: RAG 系统完成 | Week 3 | 可检索的知识库 API |
| M2: 单 Agent 完成 | Week 7 | 4 个独立 Agent 可运行 |
| M3: 编排完成 | Week 10 | LangGraph 多 Agent 协作 |
| M4: 生产就绪 | Week 13 | 完整测试 + 文档 |
| M5: 上线 | Week 16 | 生产环境运行 |

### 8.3 交付物清单

- [ ] 架构设计文档
- [ ] API 接口文档
- [ ] 部署运维手册
- [ ] 测试报告
- [ ] 性能基准报告
- [ ] 用户使用手册
- [ ] 源代码仓库

---

## 附录

### A. 依赖清单

```
# requirements.txt
# Core Framework
langgraph>=0.2.50
langchain>=0.3.0
langchain-anthropic>=0.2.0
langchain-community>=0.3.0

# LLM Providers
anthropic>=0.40.0
openai>=1.50.0

# Web Framework
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
websockets>=13.0

# Database
asyncpg>=0.29.0
redis>=5.2.0
psycopg2-binary>=2.9.0

# Vector & Embedding
sentence-transformers>=3.0.0
FlagEmbedding>=1.2.0

# Task Queue
celery>=5.4.0
kombu>=5.4.0

# Monitoring & Observability
langsmith>=0.1.0
prometheus-client>=0.21.0
opentelemetry-api>=1.27.0

# Utilities
pydantic>=2.9.0
pydantic-settings>=2.5.0
python-dotenv>=1.0.0
httpx>=0.27.0
tenacity>=9.0.0
```

### B. 环境变量

```bash
# .env.example
# Database
DATABASE_URL=postgresql://user:pass@localhost:15433/i3d_multitenant
REDIS_URL=redis://localhost:6379/0

# LLM API
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Observability
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=i3d-agent-production

# Services
SEARCH_SERVICE_URL=http://localhost:18000
ANALYSIS_SERVICE_URL=http://localhost:28000
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Features
ENABLE_RAG=true
ENABLE_STREAMING=true
ENABLE_CACHING=true

# Performance
MAX_CONCURRENT_REQUESTS=100
CACHE_TTL_SECONDS=3600
```

### C. 参考资料

1. [Microsoft Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/overview/)
2. [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
3. [LangChain State of Agent Engineering Report 2026](https://www.langchain.com/state-of-agent-engineering)
4. [Anthropic Claude API Documentation](https://docs.anthropic.com/)
5. [OpenAI Swarm GitHub](https://github.com/openai/swarm)
6. [CrewAI Documentation](https://docs.crewai.com/)

---

**文档变更记录**

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0 | 2026-05-13 | - | 初始版本 |
