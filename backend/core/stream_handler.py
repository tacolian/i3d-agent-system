"""
流式响应处理器
处理SSE和WebSocket流式输出
"""
from typing import AsyncIterator, Dict, Any, Optional
import json
import asyncio

from ..models.schema import StreamChunk


class StreamHandler:
    """
    流式响应处理器

    支持:
    1. SSE (Server-Sent Events)
    2. WebSocket
    3. 流式JSON
    """

    CONTENT_TYPE_SSE = "text/event-stream"
    CONTENT_TYPE_STREAM_JSON = "application/x-ndjson"

    @staticmethod
    async def to_sse(
        chunks: AsyncIterator[StreamChunk],
    ) -> AsyncIterator[str]:
        """
        将响应块转换为SSE格式

        Args:
            chunks: 响应块迭代器

        Yields:
            SSE格式的字符串
        """
        async for chunk in chunks:
            data = chunk.model_dump_json(exclude_none=True)
            yield f"data: {data}\n\n"

        # 发送结束事件
        yield "data: [DONE]\n\n"

    @staticmethod
    async def to_stream_json(
        chunks: AsyncIterator[StreamChunk],
    ) -> AsyncIterator[str]:
        """
        将响应块转换为流式JSON格式

        Args:
            chunks: 响应块迭代器

        Yields:
            JSON格式的字符串（每行一个JSON对象）
        """
        async for chunk in chunks:
            yield chunk.model_dump_json(exclude_none=True) + "\n"

    @staticmethod
    async def to_websocket(
        chunks: AsyncIterator[StreamChunk],
        websocket,
    ) -> None:
        """
        将响应块发送到WebSocket

        Args:
            chunks: 响应块迭代器
            websocket: WebSocket连接对象
        """
        async for chunk in chunks:
            await websocket.send_json(chunk.model_dump(exclude_none=True))

        # 发送结束消息
        await websocket.send_json({"type": "done"})

    @staticmethod
    def parse_sse_line(line: str) -> Optional[Dict[str, Any]]:
        """
        解析SSE数据行

        Args:
            line: SSE数据行

        Returns:
            解析后的数据，如果解析失败返回None
        """
        if not line.startswith("data: "):
            return None

        data = line[6:]  # 去掉 "data: " 前缀

        if data == "[DONE]":
            return {"done": True}

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    @staticmethod
    async def collect_stream(
        chunks: AsyncIterator[StreamChunk],
    ) -> tuple[str, list[Dict[str, Any]], list[Dict[str, Any]]]:
        """
        收集流式响应的完整内容

        Args:
            chunks: 响应块迭代器

        Returns:
            (完整响应, 工具调用列表, 元数据列表)
        """
        full_response = ""
        tool_calls = []
        metadata_list = []

        async for chunk in chunks:
            if chunk.chunk_type == "content" and chunk.content:
                full_response += chunk.content
            elif chunk.chunk_type == "tool_call" and chunk.tool_call:
                tool_calls.append(chunk.tool_call.model_dump())
            elif chunk.chunk_type == "metadata" and chunk.metadata:
                metadata_list.append(chunk.metadata)

        return full_response, tool_calls, metadata_list


class StreamWriter:
    """
    流式写入器
    用于构建流式响应
    """

    def __init__(self):
        self._queue: asyncio.Queue[Optional[StreamChunk]] = asyncio.Queue()

    async def write(self, chunk: StreamChunk) -> None:
        """写入一个响应块"""
        await self._queue.put(chunk)

    async def write_content(self, content: str) -> None:
        """写入内容块"""
        await self.write(StreamChunk(
            chunk_type="content",
            content=content,
        ))

    async def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """写入元数据块"""
        await self.write(StreamChunk(
            chunk_type="metadata",
            metadata=metadata,
        ))

    async def write_error(self, error: str) -> None:
        """写入错误块"""
        await self.write(StreamChunk(
            chunk_type="error",
            error=error,
        ))

    async def close(self) -> None:
        """关闭写入器"""
        await self._queue.put(None)

    def __aiter__(self):
        """支持异步迭代"""
        return self

    async def __anext__(self):
        """异步迭代下一个块"""
        chunk = await self._queue.get()
        if chunk is None:
            raise StopAsyncIteration
        return chunk
