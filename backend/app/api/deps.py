from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import decode_access_token
from app.core.rate_limiter import rate_limiter

security_bearer = HTTPBearer(auto_error=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária. Envie o token Bearer.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_email = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if not user_email or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token com claims inválidos."
        )

    stmt = select(User).where(User.email == user_email, User.tenant_id == tenant_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo ou inexistente."
        )
    return user

async def verify_rate_limit(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforces distributed token bucket rate limiting per tenant."""
    identifier = f"tenant:{current_user.tenant_id}"
    allowed, remaining, retry_after = await rate_limiter.check_rate_limit(identifier)
    request.state.rate_limit_limit = "60"
    request.state.rate_limit_remaining = str(remaining)

    response.headers["X-RateLimit-Limit"] = "60"
    response.headers["X-RateLimit-Remaining"] = str(remaining)

    if not allowed:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Cota de requisições excedida para o tenant. Tente novamente em {retry_after} segundos.",
            headers={"Retry-After": str(retry_after)}
        )
    return current_user
