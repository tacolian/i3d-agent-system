# i3d-agent-system

3D CAD智能检索Agent系统 - 基于LangGraph的多Agent协作系统

## 项目简介

本项目实现了基于LangGraph的多Agent协作系统，用于3D CAD模型的智能检索、分析、推荐和问答。系统采用RAG（检索增强生成）技术，结合向量检索和关键词检索，提供准确的模型检索和智能问答能力。

### 核心特性

- **多Agent协作**: 4个专业Agent（搜索、分析、推荐、问答）协同工作
- **智能路由**: 根据任务复杂度自动选择最合适的LLM模型
- **混合检索**: 结合BM25和向量检索，提高检索准确率
- **流式响应**: 支持SSE和WebSocket流式输出
- **多租户**: 基于PostgreSQL RLS的租户隔离
- **可观测**: LangSmith集成和Prometheus监控

## 架构

```
┌─────────────────────────────────────────────────┐
│                  FastAPI Layer                  │
├─────────────────────────────────────────────────┤
│              Agent Controller (LangGraph)        │
├─────────────────────────────────────────────────┤
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐│
│  │ Search │  │Analysis│ │Recommend│ │   QA   ││
│  │ Agent  │  │ Agent  │ │  Agent  │ │ Agent  ││
│  └────────┘  └────────┘  └────────┘  └────────┘│
├─────────────────────────────────────────────────┤
│                 RAG Engine                       │
│  (Hybrid Search: BM25 + Vector + Reranker)      │
├─────────────────────────────────────────────────┤
│  PostgreSQL + pgvector  │  Redis  │  RabbitMQ   │
└─────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 15+ with pgvector
- Redis 7+
- RabbitMQ 3+

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

### 运行

```bash
# 启动服务
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker部署

```bash
cd docker
docker-compose up -d
```

## API使用

### 聊天接口

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: shenfa" \
  -d '{
    "query": "搜索一个法兰盘模型",
    "stream": false
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

### 代码格式化

```bash
# 格式化代码
black backend/

# 检查代码
ruff check backend/
```

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
├── config/                # 配置文件
├── docker/                # Docker配置
└── requirements.txt       # Python依赖
```

## 许可证

MIT License
