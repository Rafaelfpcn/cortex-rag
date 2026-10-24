from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.api.deps import get_db, verify_rate_limit
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentResponse, DocumentListResponse, UploadResponse, DocumentChunkResponse
from app.services.ingestion_service import ingestion_service

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    current_user: User = Depends(verify_rate_limit),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo sem nome fornecido.")

    # Validate file extension
    allowed_extensions = (".txt", ".md", ".json", ".csv", ".pdf")
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Extensão não suportada. Formatos aceitos: {', '.join(allowed_extensions)}"
        )

    # Read content
    raw_bytes = await file.read()
    if len(raw_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="Arquivo excede o limite máximo de 10MB.")

    # Text extraction (handling utf-8 text or basic binary extraction)
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = raw_bytes.decode("latin-1", errors="replace")

    doc_title = title or file.filename
    doc, is_duplicate = await ingestion_service.process_document(
        db=db,
        tenant_id=current_user.tenant_id,
        title=doc_title,
        file_name=file.filename,
        content=content
    )

    msg = "Documento já indexado anteriormente (idempotência garantida)." if is_duplicate else "Documento indexado com sucesso."
    return UploadResponse(
        document_id=doc.id,
        file_name=doc.file_name,
        status=doc.status,
        message=msg
    )

@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(verify_rate_limit),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Document)
        .where(Document.tenant_id == current_user.tenant_id)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=len(docs)
    )

@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(verify_rate_limit),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.tenant_id == current_user.tenant_id
        )
        .order_by(DocumentChunk.chunk_index.asc())
    )
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    return [
        DocumentChunkResponse(
            id=c.id,
            chunk_index=c.chunk_index,
            content=c.content,
            meta=c.meta,
            created_at=c.created_at
        )
        for c in chunks
    ]

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(verify_rate_limit),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == current_user.tenant_id
    )
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    await db.delete(doc)
    await db.commit()
    return {"message": "Documento e chunks removidos com sucesso."}
