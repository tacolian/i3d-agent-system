"""
文档上传API路由
"""
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel

from ...models.schema import TenantContext
from ...rag.document_processor import get_document_processor
from ...config import settings
from ..deps import get_tenant_context

router = APIRouter(prefix="/api/documents", tags=["documents"])


class UploadResponse(BaseModel):
    """上传响应"""
    success: bool
    file_name: str
    chunks_processed: int
    message: str


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_context),
):
    """
    上传文档并处理

    支持的文件格式:
    - 文本文件: .txt, .md
    - PDF: .pdf
    - Word: .doc, .docx
    - Excel: .xls, .xlsx
    """
    # 验证文件大小
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes",
        )

    # 保存临时文件
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=os.path.splitext(file.filename or "")[1],
    ) as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        # 处理文档
        processor = get_document_processor()
        chunks = await processor.process_document(
            file_path=tmp_file_path,
            tenant_id=str(tenant_id),
            metadata={
                "file_name": file.filename,
                "file_type": file.content_type,
                "size": len(content),
            },
        )

        return UploadResponse(
            success=True,
            file_name=file.filename or "unknown",
            chunks_processed=len(chunks),
            message=f"Successfully processed {len(chunks)} chunks",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}",
        )

    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_file_path)
        except:
            pass


@router.post("/upload/batch")
async def upload_documents_batch(
    files: List[UploadFile] = File(...),
    tenant_id: str = Depends(get_tenant_context),
):
    """
    批量上传文档
    """
    results = []

    for file in files:
        try:
            result = await upload_document(file, tenant_id)
            results.append({
                "file_name": file.filename,
                "success": True,
                "result": result,
            })
        except Exception as e:
            results.append({
                "file_name": file.filename,
                "success": False,
                "error": str(e),
            })

    return {
        "total": len(files),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
    }
