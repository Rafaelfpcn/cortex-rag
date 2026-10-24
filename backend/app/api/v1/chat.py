from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.api.deps import get_db, verify_rate_limit
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.models.query_log import QueryLog
from app.schemas.chat import ChatQueryRequest, SystemMetrics
from app.services.rag_engine import rag_engine

router = APIRouter(prefix="/chat", tags=["Chat & RAG"])

@router.post("/stream")
async def chat_stream(
    req: ChatQueryRequest,
    request: Request,
    current_user: User = Depends(verify_rate_limit),
    db: AsyncSession = Depends(get_db)
):
    """
    Server-Sent Events (SSE) streaming endpoint for RAG.
    Streams token-by-token response with citations and semantic cache indicators.
    """
    limit_val = getattr(request.state, "rate_limit_limit", "60")
    rem_val = getattr(request.state, "rate_limit_remaining", "60")

    return StreamingResponse(
        rag_engine.answer_stream(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            query=req.query,
            document_ids=req.document_ids
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-RateLimit-Limit": limit_val,
            "X-RateLimit-Remaining": rem_val,
        }
    )

@router.get("/metrics", response_model=SystemMetrics)
async def get_metrics(
    current_user: User = Depends(verify_rate_limit),
    db: AsyncSession = Depends(get_db)
):
    # Total queries and cache hits for this tenant
    q_stmt = select(
        func.count(QueryLog.id),
        func.sum(case((QueryLog.cache_hit == True, 1), else_=0)),
        func.avg(QueryLog.latency_ms)
    ).where(QueryLog.tenant_id == current_user.tenant_id)
    
    q_res = await db.execute(q_stmt)
    total_q, cache_hits, avg_lat = q_res.first()
    total_q = total_q or 0
    cache_hits = cache_hits or 0
    avg_lat = round(float(avg_lat or 0.0), 2)
    hit_rate = round((cache_hits / total_q * 100), 1) if total_q > 0 else 0.0

    # Total documents and chunks
    d_stmt = select(func.count(Document.id)).where(Document.tenant_id == current_user.tenant_id)
    d_count = (await db.execute(d_stmt)).scalar() or 0

    c_stmt = select(func.count(DocumentChunk.id)).where(DocumentChunk.tenant_id == current_user.tenant_id)
    c_count = (await db.execute(c_stmt)).scalar() or 0

    return SystemMetrics(
        total_queries=total_q,
        cache_hits=cache_hits,
        cache_hit_rate_pct=hit_rate,
        avg_latency_ms=avg_lat,
        total_documents=d_count,
        total_chunks=c_count
    )
