# i3d-agent-system Agent 指南

> 本文档供 AI Coding Agent 阅读。项目使用中文注释和文档，本文件同样使用中文撰写。

## 项目概述

**i3d-agent-system**（3D CAD 智能检索 Agent 系统）是一个基于 LangGraph 的多 Agent 协作后端服务，用于 3D CAD 模型的智能检索、分析、推荐和问答。系统采用 RAG（检索增强生成）技术，结合向量检索与关键词检索，提供准确的模型检索和智能问答能力。

### 核心特性

- **多 Agent 协作**：4 个专业 Agent（搜索、分析、推荐、问答）协同工作
- **智能路由**：根据任务复杂度自动选择最合适的 LLM 模型（Claude / OpenAI）
- **混合检索**：结合 BM25 和向量检索（pgvector），支持重排序（Reranker）
- **流式响应**：支持 SSE 流式输出
- **多租户**：基于 PostgreSQL RLS 的租户隔离，支持 `shenfa`、`meidi`、`dongjiang`、`huabei`
- **可观测性**：LangSmith 集成 + Prometheus 监控 + Grafana 可视化

### 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| Agent 编排 | LangGraph + LangChain |
| LLM 提供商 | Anthropic (Claude) / OpenAI (GPT) |
| 数据库 | PostgreSQL 15 + pgvector |
| 缓存/消息 | Redis 7 / RabbitMQ 3 |
| 对象存储 | MinIO |
| 配置管理 | Pydantic Settings + YAML |
| 监控 | Prometheus + Grafana + OpenTelemetry |

## 项目结构

```
i3d-agent-system/
├── backend/                    # 后端代码（主代码目录）
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # Pydantic Settings 配置管理
│   ├── agents/                 # Agent 实现
│   │   ├── base.py             # Agent 基类（AgentInput / AgentOutput / BaseAgent）
│   │   ├── search_agent.py     # 搜索 Agent
│   │   ├── analysis_agent.py   # 分析 Agent
│   │   ├── recommendation_agent.py  # 推荐 Agent
│   │   └── qa_agent.py         # 问答 Agent
│   ├── api/                    # API 路由层
│   │   ├── deps.py             # FastAPI 依赖（租户上下文、API Key 验证）
│   │   └── routes/             # 路由模块
│   │       ├── chat.py         # 聊天接口（/api/chat/、/api/chat/stream）
│   │       ├── health.py       # 健康检查
│   │       └── upload.py       # 文档上传
│   ├── core/                   # 核心业务逻辑
│   │   ├── agent_controller.py # Agent 控制器（编排工作流执行）
│   │   ├── llm_router.py       # LLM 智能路由（根据复杂度选模型）
│   │   ├── state_manager.py    # 状态管理
│   │   └── stream_handler.py   # 流式响应处理
│   ├── db/                     # 数据库层
│   │   ├── session.py          # 异步会话 / 连接池
│   │   └── repositories.py     # 数据仓库（向量检索等）
│   ├── graph/                  # LangGraph 工作流定义
│   │   ├── workflow.py         # AgentWorkflow（状态图编排）
│   │   ├── nodes.py            # 工作流节点（意图识别、检索、Agent 执行等）
│   │   ├── edges.py            # 条件路由边
│   │   └── state.py            # AgentState 状态定义
│   ├── models/                 # 数据模型
│   │   ├── schema.py           # Pydantic 请求/响应模型
│   │   └── enums.py            # 枚举定义（IntentType、AgentType、ToolType 等）
│   ├── rag/                    # RAG 系统
│   │   ├── document_processor.py  # 文档处理
│   │   ├── embeddings.py       # Embedding 服务
│   │   ├── hybrid_search.py    # 混合检索（BM25 + Vector）
│   │   ├── reranker.py         # 重排序器
│   │   └── retriever.py        # 检索器封装
│   ├── services/               # 服务层
│   │   ├── cache_service.py    # Redis 缓存
│   │   ├── mq_service.py       # RabbitMQ 消息队列
│   │   └── tenant_service.py   # 租户服务
│   ├── tests/                  # 测试
│   │   ├── conftest.py         # Pytest 全局 fixture
│   │   ├── unit/               # 单元测试
│   │   └── integration/        # 集成测试
│   ├── tools/                  # Agent 工具
│   │   ├── cad_search.py       # CAD 模型搜索
│   │   ├── similarity_search.py # 相似度搜索
│   │   ├── metadata_query.py   # 元数据查询
│   │   └── file_analyzer.py    # 文件分析
│   └── utils/                  # 工具函数
│       ├── logger.py           # 日志配置（JSON / text 格式）
│       ├── tracer.py           # 链路追踪
│       └── helpers.py          # 通用辅助函数
├── config/
│   └── settings.yaml           # YAML 格式多环境配置
├── docker/
│   ├── Dockerfile              # 多阶段构建
│   ├── docker-compose.yml      # 全栈编排（API + DB + Redis + MQ + 监控）
│   └── prometheus.yml          # Prometheus 配置
├── pyproject.toml              # 项目元数据 + 工具配置（Black / Ruff / Mypy / Pytest）
└── requirements.txt            # 精确版本依赖（与 pyproject.toml 互补）
```

## 构建与运行

### 环境要求

- Python >= 3.11
- PostgreSQL 15+ with pgvector
- Redis 7+
- RabbitMQ 3+

### 安装依赖

```bash
# 使用 requirements.txt（推荐，版本锁定）
pip install -r requirements.txt

# 或使用 pyproject.toml（开发模式）
pip install -e ".[dev]"
```

### 配置环境变量

创建 `.env` 文件（项目根目录）：

```bash
# LLM API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
LANGCHAIN_API_KEY=your_langchain_api_key

# Database
DATABASE_URL=postgresql+asyncpg://app_user:password@localhost:15433/i3d_multitenant

# Redis
REDIS_URL=redis://localhost:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

> 配置优先级：环境变量 > `.env` 文件 > `config/settings.yaml` > 代码默认值。
> 实际配置由 `backend/config.py` 中的 `pydantic_settings.BaseSettings` 统一管理。

### 运行服务

```bash
# 开发模式（热重载）
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 或通过 main.py 直接运行
python backend/main.py
```

### Docker 部署

```bash
cd docker
docker-compose up -d
```

Docker Compose 会启动以下服务：
- `agent-api`（端口 8000）
- `postgres`（端口 15433，含 pgvector）
- `redis`（端口 6379）
- `rabbitmq`（端口 5672 / 15672）
- `prometheus`（端口 9090）
- `grafana`（端口 3000）

## 测试

### 运行测试

```bash
# 运行全部测试（含覆盖率报告）
pytest backend/tests -v

# 单元测试
pytest backend/tests/unit -v

# 集成测试（需要真实服务或适当 mock）
pytest backend/tests/integration -v

# 覆盖率 HTML 报告
pytest --cov=backend --cov-report=html
```

### 测试配置（pyproject.toml）

- 测试根目录：`backend/tests`
- 异步模式：`auto`（pytest-asyncio）
- 默认带覆盖率：`--cov=backend --cov-report=html`
- 文件/类/函数命名遵循标准 `test_*.py` / `Test*` / `test_*`

### 测试注意事项

- 集成测试使用 `httpx.ASGITransport` 直接测试 FastAPI app，无需启动真实服务。
- `conftest.py` 提供了 `event_loop`（session 级）、`database`、`db_session`、`sample_tenant_id` 等 fixture。
- 单元测试中对 LLM 调用应使用 `monkeypatch` mock `_call_llm` 方法，避免真实 API 调用。
- 测试数据库默认指向 `i3d_test`。

## 代码风格

项目使用以下工具进行代码格式化和静态检查：

| 工具 | 配置位置 | 说明 |
|------|----------|------|
| **Black** | `pyproject.toml` `[tool.black]` | 行宽 100，目标 Python 3.11 |
| **Ruff** | `pyproject.toml` `[tool.ruff]` | 行宽 100，启用 E/F/I/N/W/UP |
| **Mypy** | `pyproject.toml` `[tool.mypy]` | 严格模式，`disallow_untyped_defs = true` |

### 常用命令

```bash
# 格式化代码
black backend/

# 检查代码风格
ruff check backend/

# 类型检查
mypy backend/
```

### 编码约定

- 所有模块文件顶部包含中文文档字符串，说明模块职责。
- 函数和类使用中文 docstring，Args / Returns 格式清晰。
- 类型注解强制要求（mypy `disallow_untyped_defs = true`）。
- 异步优先：数据库操作、Agent 执行、API 处理均使用 `async/await`。
- 单例模式：核心组件（AgentWorkflow、AgentController、LLMRouter）使用模块级全局变量 + getter 函数实现懒加载单例。
- 配置集中管理：`backend/config.py` 中的 `Settings` 类统一读取环境变量和 `.env`，业务代码通过 `from backend.config import settings` 访问。

## 架构关键细节

### Agent 工作流（LangGraph）

`backend/graph/workflow.py` 定义了完整的状态图：

1. **intent** → 意图识别
2. **retrieval** → 检索（混合搜索）
3. 条件路由到 4 个 Agent 之一：
   - `search_agent` → 搜索 Agent
   - `analysis_agent` → 分析 Agent
   - `recommendation_agent` → 推荐 Agent
   - `qa_agent` → 问答 Agent
4. **synthesizer** → 综合响应
5. **END**

附加节点：`clarification`（澄清需求）、`error_handler`（错误处理）。

### LLM 智能路由

`backend/core/llm_router.py` 根据任务复杂度自动选择模型层级：

| Agent 类型 | 默认层级 |
|-----------|---------|
| QA Agent | FAST (Claude Haiku / GPT-4o-mini) |
| Search Agent | BALANCED (Claude Sonnet / GPT-4o) |
| Analysis Agent | COMPLEX (Claude Opus / GPT-4-turbo) |
| Recommendation Agent | BALANCED |

> 输入长度超过 10000 字符时自动升级层级；可通过 `cost_sensitivity` 降级。

### 多租户

- 租户通过 HTTP Header `X-Tenant-ID` 传递，由 `api/deps.py` 中的 `get_tenant_context` 提取并校验。
- 有效租户列表在 `settings.SUPPORTED_TENANTS` 中定义（默认：`shenfa`, `meidi`, `dongjiang`, `huabei`）。
- 向量表按租户隔离：`tenant_{tenant_id}_vectors`。
- MinIO 桶名按租户隔离：`{tenant_id}-files`。

### RAG 检索流程

1. 用户查询同时进入 **向量检索**（pgvector + text-embedding-3-small）和 **BM25 检索**
2. 结果按权重合并：`final_score = 0.7 * vector_score + 0.3 * bm25_score`
3. 过滤低于相似度阈值（默认 0.7）的结果
4. 可选重排序（Cohere Rerank / BGE Reranker）
5. 返回 Top-K（默认 10，重排序后 5）

## 安全注意事项

- **API Key 验证**：`api/deps.py` 中的 `verify_api_key` 目前为简化实现，仅对比 `SECRET_KEY`。生产环境应加强密钥管理。
- **CORS**：默认允许所有来源（`ALLOWED_ORIGINS = ["*"]`），生产环境应收紧。
- **租户隔离**：依赖 PostgreSQL RLS 和代码层面的表名/桶名隔离，确保数据不跨租户泄漏。
- **MinIO 配置**：`MINIO_ENDPOINT` 默认为内网地址 `172.16.45.33:9000`，生产部署需确认网络可达性。
- **LangSmith**：默认启用追踪（`LANGCHAIN_TRACING_V2 = true`），注意避免敏感数据被发送到第三方平台。

## 开发注意事项

- **Python 版本**：必须 >= 3.11（使用 `py311` target）。
- **依赖管理**：`requirements.txt` 锁定精确版本，`pyproject.toml` 定义兼容范围。更新依赖时建议同步维护两者。
- **Dockerfile 路径**：`docker/Dockerfile` 中 `COPY backend/requirements.txt .` 预期构建上下文为项目根目录（`docker-compose.yml` 中 `context: ..`）。
- **日志**：支持 JSON 和 text 两种格式，通过 `LOG_FORMAT` 控制，默认 JSON。日志目录 `./logs`。
- **健康检查**：`GET /health/ping` 用于 Docker HEALTHCHECK 和负载均衡探活。
