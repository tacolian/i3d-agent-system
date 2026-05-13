"""
RabbitMQ消息队列服务
"""
from typing import Optional, Any, Callable
import aio_pika
import asyncio
import json

from ..config import settings


class MQService:
    """
    RabbitMQ消息队列服务

    功能:
    1. 发布消息
    2. 消费消息
    3. RPC调用
    """

    def __init__(self):
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.RobustChannel] = None

    async def _get_connection(self) -> aio_pika.RobustConnection:
        """获取连接"""
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
            )
        return self._connection

    async def _get_channel(self) -> aio_pika.RobustChannel:
        """获取通道"""
        if self._channel is None or self._channel.is_closed:
            connection = await self._get_connection()
            self._channel = await connection.channel()
        return self._channel

    async def publish(
        self,
        queue_name: str,
        message: Any,
        exchange: str = "",
    ) -> None:
        """
        发布消息

        Args:
            queue_name: 队列名
            message: 消息内容（会被JSON序列化）
            exchange: 交换机名
        """
        channel = await self._get_channel()

        if exchange:
            ex = await channel.get_exchange(exchange)
        else:
            ex = channel.default_exchange

        await ex.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                content_type="application/json",
            ),
            routing_key=queue_name,
        )

    async def consume(
        self,
        queue_name: str,
        callback: Callable,
        auto_ack: bool = False,
    ) -> None:
        """
        消费消息

        Args:
            queue_name: 队列名
            callback: 回调函数
            auto_ack: 是否自动确认
        """
        channel = await self._get_channel()

        # 声明队列
        queue = await channel.declare_queue(
            queue_name,
            durable=True,
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    body = json.loads(message.body.decode())
                    await callback(body)
                    if not auto_ack:
                        await message.ack()
                except Exception as e:
                    await message.reject(requeue=False)
                    raise

    async def rpc_call(
        self,
        queue_name: str,
        message: Any,
        timeout: float = 30.0,
    ) -> Any:
        """
        RPC调用

        Args:
            queue_name: 队列名
            message: 请求消息
            timeout: 超时时间

        Returns:
            响应消息
        """
        channel = await self._get_channel()

        # 声明回调队列
        callback_queue = await channel.declare_queue(exclusive=True)

        # 创建协程用于接收响应
        response_future = asyncio.Future()

        async def on_response(message: aio_pika.IncomingMessage):
            async with message.process():
                if message.correlation_id:
                    response_future.set_result(
                        json.loads(message.body.decode())
                    )

        # 消费回调队列
        await callback_queue.consume(on_response)

        # 发送请求
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                content_type="application/json",
                reply_to=callback_queue.name,
                correlation_id=str(id(message)),
            ),
            routing_key=queue_name,
        )

        # 等待响应
        return await asyncio.wait_for(response_future, timeout)

    async def ping(self) -> bool:
        """Ping RabbitMQ"""
        try:
            connection = await self._get_connection()
            return not connection.is_closed
        except:
            return False

    async def close(self) -> None:
        """关闭连接"""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()


# ============================================================================
# 全局实例
# ============================================================================

_mq_service: Optional[MQService] = None


def get_mq_service() -> MQService:
    """获取MQ服务单例"""
    global _mq_service
    if _mq_service is None:
        _mq_service = MQService()
    return _mq_service
