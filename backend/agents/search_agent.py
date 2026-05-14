"""
搜索Agent
负责处理CAD模型搜索请求
"""
from typing import Dict, Any, List, Optional
import time

from langchain_core.messages import SystemMessage, HumanMessage

from .base import BaseAgent, AgentInput, AgentOutput
from ..models.enums import AgentType
from ..tools.cad_search import cad_search_tool, CadSearchParams
from ..tools.similarity_search import similarity_search_tool


class SearchAgent(BaseAgent):
    """
    搜索Agent

    职责:
    1. 理解用户的搜索需求
    2. 调用合适的搜索工具
    3. 格式化并返回搜索结果
    4. 提供搜索建议
    """

    def __init__(self):
        super().__init__(agent_type=AgentType.SEARCH)

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个3D CAD模型搜索专家助手。

你的职责是帮助用户搜索和查找CAD模型。

## 工作流程

1. 理解用户的搜索需求
2. 调用搜索工具查找相关模型
3. 以清晰、有条理的方式呈现结果
4. 提供相关的搜索建议

## 输出格式

请按照以下格式输出:

### 搜索结果
[列出找到的CAD模型，包含文件名、相似度、关键信息]

### 详细信息
[对每个模型的详细描述]

### 建议
[提供相关的搜索建议或相似模型推荐]

## 注意事项

- 如果搜索结果较少，建议用户尝试不同的关键词
- 如果结果不相关，建议用户澄清需求
- 突出显示高相似度（>0.8）的结果
"""

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        执行搜索Agent逻辑

        Args:
            input_data: Agent输入

        Returns:
            Agent输出
        """
        start_time = time.time()

        query = input_data.query
        tenant_id = input_data.tenant_id
        max_results = input_data.max_results or 10

        # 判断是否需要调用外部服务
        # 如果 search_results 为空，需要调用工具进行搜索
        search_results = input_data.search_results
        tool_used = None

        if not search_results or len(search_results) == 0:
            # 判断是相似度搜索还是普通搜索
            is_similarity = any(kw in query.lower() for kw in ["相似", "类似", "similar", "like"])

            if is_similarity:
                # 使用相似度搜索工具
                result = await similarity_search_tool(
                    query=query,
                    tenant_id=tenant_id,
                    top_k=max_results,
                )
                tool_used = "similarity_search"
            else:
                # 使用CAD搜索工具
                params = CadSearchParams(
                    query=query,
                    tenant_id=tenant_id,
                    top_k=max_results,
                )
                result = await cad_search_tool(params)
                tool_used = "cad_search"

            if result.get("success"):
                search_results = result.get("results", [])

        # 构建上下文信息
        additional_context = f"使用的搜索工具: {tool_used}" if tool_used else ""

        # 构建消息
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=self._format_context(
                query=query,
                search_results=search_results,
                additional_context=additional_context,
            )),
        ]

        # 调用LLM生成响应
        response = await self._call_llm(messages, temperature=0.5)

        # 生成建议
        suggestions = self._generate_suggestions(
            query=query,
            search_results=search_results,
        )

        # 收集工具调用记录
        tool_calls = []
        if tool_used:
            tool_calls.append({
                "tool_name": tool_used,
                "arguments": {"query": query, "top_k": max_results},
                "result": f"找到 {len(search_results)} 个结果" if search_results else "未找到结果",
                "duration_ms": result.get("duration_ms", 0),
            })

        duration = (time.time() - start_time) * 1000

        return AgentOutput(
            response=response,
            agent_type=self.agent_type,
            tool_calls=tool_calls,
            suggestions=suggestions,
            metadata={
                "duration_ms": duration,
                "result_count": len(search_results),
                "tool_used": tool_used,
            },
        )

    def _generate_suggestions(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
    ) -> List[str]:
        """
        生成搜索建议

        Args:
            query: 原始查询
            search_results: 搜索结果

        Returns:
            建议列表
        """
        suggestions = []

        # 如果结果较少，建议扩展搜索
        if len(search_results) < 3:
            suggestions.append("尝试使用更通用的关键词搜索")
            suggestions.append("可以浏览模型分类目录")

        # 如果结果较多，建议细化
        elif len(search_results) > 20:
            suggestions.append("可以添加更多细节来缩小搜索范围")
            suggestions.append("使用特定的参数或属性进行过滤")

        # 基于查询内容的建议
        if any(keyword in query.lower() for keyword in ["零件", "part"]):
            suggestions.append("查看相关装配体可能更有帮助")

        if any(keyword in query.lower() for keyword in ["相似", "类似", "similar"]):
            suggestions.append("可以上传参考模型进行相似度搜索")

        return suggestions
