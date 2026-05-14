# I3D Agent System

> 3D CAD智能检索Agent系统 - 基于LangGraph的多Agent协作系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 项目简介

本项目是一个基于 **LangGraph** 的多 Agent 协作系统，专为 3D CAD 模型的智能检索、分析、推荐和问答设计。系统采用 **RAG（检索增强生成）** 技术，结合向量检索和关键词检索，提供准确的模型检索和智能问答能力。

### 核心特性

- **多Agent协作**: 4个专业Agent（搜索、分析、推荐、问答）协同工作
- **智能路由**: 根据任务复杂度自动选择最合适的LLM模型
- **混合检索**: 结合BM25和向量检索，提高检索准确率
- **流式响应**: 支持SSE流式输出，实时返回结果
- **多租户**: 基于PostgreSQL RLS的租户数据隔离
- **可观测**: LangSmith集成和Prometheus监控支持

---

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                  前端 (Vue 3)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ 聊天界面 │  │ 文档上传 │  │ 系统状态 │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
                      │ HTTP/SSE
┌─────────────────────────────────────────────────┐
│              FastAPI 后端服务                    │
│  ┌──────────────────────────────────────────┐  │
│  │           Agent Controller               │  │
│  └──────────────────────────────────────────┘  │
│                      │                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────┐│
│  │ LangGraph    │  │ 工具层       │  │ RAG  ││
│  │ 工作流编排   │  │ Tool Calls   │  │ 引擎 ││
│  └──────────────┘  └──────────────┘  └──────┘│
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│              外部微服务                          │
│  ┌──────────────────┐  ┌──────────────────┐    │
│  │InferEngineer-3d  │  │  3d-search-core  │    │
│  │   :18000         │  │    :28000        │    │
│  └──────────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│              数据存储层                          │
│  PostgreSQL+pgvector  │  Redis  │  MinIO       │
└─────────────────────────────────────────────────┘
```

---

## 功能说明

### 后端功能

#### 1. 多Agent系统

| Agent | 功能描述 | 调用工具 | 外部服务 |
|-------|----------|----------|----------|
| **SearchAgent** | CAD模型语义检索 | `cad_search_tool`, `similarity_search_tool` | InferEngineer-3dRetrieval (:18000) |
| **AnalysisAgent** | 模型特征分析 | `file_analyzer_tool` | 3d-search-core (:28000) |
| **RecommendationAgent** | 相似模型推荐 | `similarity_search_tool` | 本地向量检索 |
| **QAAgent** | 知识问答 | 基于RAG上下文 | LLM推理 |

#### 2. API接口

**聊天接口**
- `POST /api/chat/` - 非流式聊天
- `POST /api/chat/stream` - SSE流式聊天
- `POST /api/chat/message` - 简化消息接口

**文档上传**
- `POST /api/documents/upload` - 单文档上传
- `POST /api/documents/upload/batch` - 批量上传

**健康检查**
- `GET /health/` - 完整健康检查
- `GET /health/ping` - 简单ping
- `GET /health/ready` - K8s就绪探针

#### 3. RAG检索系统

- **向量检索**: pgvector 语义搜索
- **BM25检索**: 关键词全文搜索
- **混合检索**: RRF (Reciprocal Rank Fusion) 结果融合
- **重排序**: Cross-Encoder 结果优化

#### 4. 工具层实现

| 工具 | 功能 | 调用方式 |
|------|------|----------|
| `cad_search_tool` | 调用外部搜索服务 | HTTP POST → localhost:18000 |
| `file_analyzer_tool` | 调用分析服务 | HTTP GET → localhost:28000 |
| `similarity_search_tool` | 本地向量相似度搜索 | pgvector |
| `metadata_query_tool` | 元数据过滤查询 | PostgreSQL |

#### 5. 核心组件

```
backend/
├── agents/           # 4个Agent实现
│   ├── search_agent.py
│   ├── analysis_agent.py
│   ├── recommendation_agent.py
│   └── qa_agent.py
├── graph/            # LangGraph工作流
│   ├── workflow.py   # 主工作流编排
│   ├── nodes.py      # 节点定义
│   ├── edges.py      # 条件路由
│   └── state.py      # 状态定义
├── tools/            # Agent工具集
│   ├── cad_search.py
│   ├── file_analyzer.py
│   ├── similarity_search.py
│   └── metadata_query.py
├── rag/              # RAG系统
│   ├── hybrid_search.py
│   ├── retriever.py
│   ├── reranker.py
│   └── embeddings.py
├── api/              # API路由
│   └── routes/
│       ├── chat.py
│       ├── upload.py
│       └── health.py
└── core/             # 核心服务
    ├── agent_controller.py
    ├── llm_router.py
    └── stream_handler.py
```

### 前端功能

#### 1. 用户界面

**租户选择**
- 支持4个租户：申发、美的、东江、华北
- 租户隔离的数据会话
- 本地持久化租户选择

**智能对话**
- 实时聊天界面
- Markdown格式支持
- 搜索结果展示
- 工具调用可视化

**文档上传**
- 拖拽上传支持
- 批量文件处理
- 上传进度显示
- 支持 .txt/.md/.pdf/.doc/.docx/.xls/.xlsx

**系统状态**
- 实时健康检查
- 服务状态监控
- API信息展示

#### 2. 交互功能

| 功能 | 说明 |
|------|------|
| 流式响应 | SSE实时推送，可开关 |
| 快捷操作 | 预设常用查询模板 |
| 会话管理 | 本地历史会话记录 |
| 设置面板 | API地址、温度、结果数等配置 |

#### 3. 前端技术栈

- **原生JavaScript** - 无框架依赖
- **SSE (Server-Sent Events)** - 流式通信
- **LocalStorage** - 状态持久化
- **CSS Grid/Flexbox** - 响应式布局

---

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 15+ with pgvector
- Redis 7+
- (可选) 外部微服务：InferEngineer-3dRetrieval、3d-search-core

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd i3d-agent-system

# 安装依赖
pip install -r requirements.txt
```

### 配置

创建 `.env` 文件：

```bash
# LLM API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
LANGCHAIN_API_KEY=your_langchain_api_key

# Database
DATABASE_URL=postgresql+asyncpg://app_user:password@localhost:15433/i3d_multitenant

# Redis
REDIS_URL=redis://localhost:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# MinIO
MINIO_ENDPOINT=172.16.45.33:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
```

### 运行

```bash
# 启动后端服务
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（使用简单HTTP服务器）
cd frontend
python -m http.server 5500
```

访问 `http://localhost:5500` 开始使用。

### Docker部署

```bash
cd docker
docker-compose up -d
```

---

## API使用示例

### 聊天接口

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: shenfa" \
  -d '{
    "query": "搜索一个法兰盘模型",
    "stream": false,
    "max_results": 10
  }'
```

### 流式响应

```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: shenfa" \
  -d '{
    "query": "搜索类似法兰盘的零件",
    "stream": true
  }'
```

### 文档上传

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "X-Tenant-ID: shenfa" \
  -F "file=@document.pdf"
```

---

## 开发

### 运行测试

```bash
# 单元测试
pytest backend/tests/unit -v

# 集成测试
pytest backend/tests/integration -v

# 带覆盖率
pytest --cov=backend --cov-report=html
```

### 代码质量

```bash
# 格式化代码
black backend/

# 检查代码
ruff check backend/

# 类型检查
mypy backend/
```

---

## 项目结构

```
i3d-agent-system/
├── backend/                # 后端代码
│   ├── agents/            # Agent实现
│   ├── api/               # API路由
│   ├── core/              # 核心业务逻辑
│   ├── db/                # 数据库层
│   ├── graph/             # LangGraph工作流
│   ├── models/            # 数据模型
│   ├── rag/               # RAG系统
│   ├── services/          # 服务层
│   ├── tests/             # 测试
│   ├── tools/             # Agent工具
│   └── utils/             # 工具函数
├── frontend/              # 前端代码
│   ├── css/               # 样式文件
│   ├── js/                # JavaScript
│   └── index.html         # 主页面
├── config/                # 配置文件
├── docker/                # Docker配置
├── scripts/               # 脚本文件
├── README.md              # 项目说明
├── requirements.txt       # Python依赖
└── pyproject.toml         # 项目配置
```

---

## 配置说明

### LLM模型路由

系统根据任务复杂度自动选择模型：

| 任务类型 | 推荐模型 | 用途 |
|----------|----------|------|
| 简单任务 | Claude Haiku | 意图识别、参数提取 |
| 标准任务 | Claude Sonnet | 复杂推理、多轮对话 |
| 复杂任务 | Claude Opus | 代码生成、数据分析 |

### RAG权重配置

- `RAG_BM25_WEIGHT`: BM25检索权重 (默认: 0.3)
- `RAG_VECTOR_WEIGHT`: 向量检索权重 (默认: 0.7)
- `RAG_SIMILARITY_THRESHOLD`: 相似度阈值 (默认: 0.7)

### 多租户配置

支持的租户：`shenfa`, `meidi`, `dongjiang`, `huabei`

租户隔离通过以下方式实现：
- PostgreSQL RLS (Row Level Security)
- 租户特定向量表：`tenant_{tenant_id}_vectors`
- 租户特定MinIO桶：`{tenant_id}-files`

---

## 许可证

MIT License
