"""
文档处理器
将上传的文档分块并向量化
"""
from typing import List, Dict, Any, Optional, AsyncIterator
from pathlib import Path
import asyncio
from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .embeddings import get_embedding_service
from ..config import settings
from ..models.schema import DocumentChunk


class DocumentProcessor:
    """
    文档处理器

    功能:
    1. 解析各种格式的文档
    2. 智能分块
    3. 向量化
    4. 存储到向量数据库
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        """
        初始化文档处理器

        Args:
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
        """
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        )

    async def process_document(
        self,
        file_path: str,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        处理单个文档

        Args:
            file_path: 文件路径
            tenant_id: 租户ID
            metadata: 文档元数据

        Returns:
            文档分块列表
        """
        # 1. 读取文档内容
        content = await self._read_file(file_path)

        # 2. 分块
        chunks = await self._split_text(content, metadata or {})

        # 3. 向量化
        embedding_service = get_embedding_service()
        for chunk in chunks:
            if chunk.embedding is None:
                chunk.embedding = await embedding_service.embed_text(chunk.content)

        # 4. 存储到向量数据库
        await self._store_chunks(chunks, tenant_id)

        return chunks

    async def process_documents(
        self,
        file_paths: List[str],
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[DocumentChunk]:
        """
        批量处理文档

        Args:
            file_paths: 文件路径列表
            tenant_id: 租户ID
            metadata: 文档元数据

        Yields:
            文档分块
        """
        tasks = [
            self.process_document(fp, tenant_id, metadata)
            for fp in file_paths
        ]

        for chunk in asyncio.as_completed(tasks):
            for doc_chunk in await chunk:
                yield doc_chunk

    async def _read_file(self, file_path: str) -> str:
        """读取文件内容"""
        path = Path(file_path)

        # 根据文件扩展名选择读取方式
        suffix = path.suffix.lower()

        if suffix in ['.txt', '.md', '.py', '.js', '.json']:
            return await self._read_text_file(path)
        elif suffix == '.pdf':
            return await self._read_pdf(path)
        elif suffix in ['.doc', '.docx']:
            return await self._read_word(path)
        elif suffix in ['.xls', '.xlsx']:
            return await self._read_excel(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    async def _read_text_file(self, path: Path) -> str:
        """读取文本文件"""
        return path.read_text(encoding='utf-8')

    async def _read_pdf(self, path: Path) -> str:
        """读取PDF文件"""
        try:
            import pypdf
            content = []
            with open(path, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        content.append(text)
            return '\n\n'.join(content)
        except ImportError:
            # 降级处理
            return path.read_text(encoding='utf-8', errors='ignore')

    async def _read_word(self, path: Path) -> str:
        """读取Word文档"""
        try:
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            result = converter.convert(str(path))
            return result.document.export_to_markdown()
        except ImportError:
            return path.read_text(encoding='utf-8', errors='ignore')

    async def _read_excel(self, path: Path) -> str:
        """读取Excel文件"""
        try:
            import pandas as pd
            df = pd.read_excel(path)
            return df.to_string()
        except ImportError:
            return path.read_text(encoding='utf-8', errors='ignore')

    async def _split_text(
        self,
        text: str,
        metadata: Dict[str, Any],
    ) -> List[DocumentChunk]:
        """分块文本"""
        # 使用LangChain文本分割器
        documents = self.text_splitter.split_text(text)

        chunks = []
        for i, doc_text in enumerate(documents):
            chunk = DocumentChunk(
                chunk_id=f"{metadata.get('file_name', 'doc')}_{i}_{datetime.now().timestamp()}",
                content=doc_text,
                metadata={
                    **metadata,
                    "chunk_index": i,
                    "chunk_size": len(doc_text),
                },
            )
            chunks.append(chunk)

        return chunks

    async def _store_chunks(
        self,
        chunks: List[DocumentChunk],
        tenant_id: str,
    ) -> None:
        """存储分块到向量数据库"""
        from ..db.repositories import VectorRepository

        vector_repo = VectorRepository(tenant_id)

        for chunk in chunks:
            await vector_repo.insert_vector(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                embedding=chunk.embedding,
                metadata=chunk.metadata,
            )


# ============================================================================
# 全局实例
# ============================================================================

_document_processor: Optional[DocumentProcessor] = None


def get_document_processor(
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> DocumentProcessor:
    """获取文档处理器单例"""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor(chunk_size, chunk_overlap)
    return _document_processor
