"""
Agent单元测试
"""
import pytest
from unittest.mock import Mock, AsyncMock

from backend.agents.search_agent import SearchAgent
from backend.agents.qa_agent import QAAgent
from backend.agents.base import AgentInput


class TestSearchAgent:
    """搜索Agent测试"""

    @pytest.fixture
    def agent(self):
        return SearchAgent()

    @pytest.fixture
    def sample_input(self, sample_tenant_id, sample_search_results):
        return AgentInput(
            query="搜索法兰盘",
            tenant_id=sample_tenant_id,
            session_id="test-session",
            search_results=sample_search_results,
        )

    @pytest.mark.asyncio
    async def test_execute(self, agent, sample_input, monkeypatch):
        """测试执行逻辑"""
        # Mock LLM调用
        async def mock_call_llm(messages, temperature=None):
            return "找到2个法兰盘模型:\n1. flange_150pn.dwg (相似度: 0.92)\n2. flange_200pn.dwg (相似度: 0.87)"

        monkeypatch.setattr(agent, "_call_llm", mock_call_llm)

        result = await agent.execute(sample_input)

        assert result.response is not None
        assert "法兰盘" in result.response
        assert result.agent_type.value == "search_agent"

    def test_get_system_prompt(self, agent):
        """测试系统提示词"""
        prompt = agent.get_system_prompt()
        assert "搜索专家" in prompt
        assert "CAD模型" in prompt


class TestQAAgent:
    """问答Agent测试"""

    @pytest.fixture
    def agent(self):
        return QAAgent()

    @pytest.fixture
    def sample_input(self, sample_tenant_id):
        return AgentInput(
            query="什么是CAD?",
            tenant_id=sample_tenant_id,
            session_id="test-session",
            search_results=[],
            context="CAD是计算机辅助设计的缩写",
        )

    @pytest.mark.asyncio
    async def test_execute(self, agent, sample_input, monkeypatch):
        """测试执行逻辑"""
        async def mock_call_llm(messages, temperature=None):
            return "CAD是计算机辅助设计（Computer-Aided Design）的缩写..."

        monkeypatch.setattr(agent, "_call_llm", mock_call_llm)

        result = await agent.execute(sample_input)

        assert result.response is not None
        assert result.agent_type.value == "qa_agent"


class TestAgentInput:
    """Agent输入测试"""

    def test_agent_input_creation(self):
        """测试输入创建"""
        input_data = AgentInput(
            query="测试查询",
            tenant_id="shenfa",
            session_id="session-123",
        )

        assert input_data.query == "测试查询"
        assert input_data.tenant_id == "shenfa"
        assert input_data.search_results == []
        assert input_data.context == ""
