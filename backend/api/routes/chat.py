"""
聊天API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from ...models.schema import (
    ChatRequest,
    ChatResponse,
    StreamChunk,
)
from ...core.agent_controller import get_agent_controller
from ...core.stream_handler import StreamHandler
from ..deps import get_tenant_context

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    tenant_context=Depends(get_tenant_context),
):
    """
    聊天接口（非流式）

    处理用户的聊天请求，返回Agent的响应
    """
    try:
        # 使用传入的租户上下文覆盖请求中的
        request.tenant_context = tenant_context

        controller = get_agent_controller()
        response = await controller.process_request(request)

        return ChatResponse(
            request_id=tenant_context.request_id or "",
            session_id=response.session_id,
            response=response,
        )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    tenant_context=Depends(get_tenant_context),
):
    """
    聊天接口（流式）

    使用SSE流式返回Agent的响应
    """
    try:
        # 使用传入的租户上下文覆盖请求中的
        request.tenant_context = tenant_context

        controller = get_agent_controller()

        # 获取流式响应
        async def generate():
            async for chunk in controller.process_request_stream(request):
                yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message")
async def send_message(
    query: str,
    session_id: Optional[str] = None,
    tenant_id: str = Depends(lambda: Depends(get_tenant_context)),
):
    """
    简化的消息发送接口

    适用于简单的测试和集成
    """
    from ...models.schema import TenantContext

    request = ChatRequest(
        query=query,
        session_id=session_id,
        tenant_context=TenantContext(tenant_id=tenant_id),
        stream=False,
    )

    controller = get_agent_controller()
    response = await controller.process_request(request)

    return {
        "response": response.response,
        "session_id": response.session_id,
        "intent": response.intent,
    }
