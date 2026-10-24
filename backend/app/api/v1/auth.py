from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.user import User, Tenant
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from app.services.ingestion_service import ingestion_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    stmt = select(User).where(User.email == req.email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado na plataforma."
        )

    # Create Tenant
    tenant = Tenant(name=req.tenant_name, plan="enterprise")
    db.add(tenant)
    await db.flush()

    # Create User
    user = User(
        tenant_id=tenant.id,
        email=req.email,
        hashed_password=get_password_hash(req.password),
        role="admin"
    )
    db.add(user)
    await db.commit()
    await db.refresh(tenant)

    token = create_access_token(subject=user.email, tenant_id=tenant.id, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=60 * 24,
        user_email=user.email,
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        role=user.role
    )

@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User, Tenant).join(Tenant, User.tenant_id == Tenant.id).where(User.email == req.email)
    res = await db.execute(stmt)
    row = res.first()

    if not row:
        raise HTTPException(status_code=400, detail="Credenciais inválidas.")

    user, tenant = row
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Credenciais inválidas.")

    token = create_access_token(subject=user.email, tenant_id=tenant.id, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=60 * 24,
        user_email=user.email,
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        role=user.role
    )

@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(db: AsyncSession = Depends(get_db)):
    """
    1-Click Recruiter/Evaluator Demo Access.
    Auto-provisions a demo tenant and seeds enterprise documentation if not present.
    """
    demo_email = "recruiter@tech.com"
    stmt = select(User, Tenant).join(Tenant, User.tenant_id == Tenant.id).where(User.email == demo_email)
    res = await db.execute(stmt)
    row = res.first()

    if not row:
        # Create Demo Tenant
        tenant = Tenant(name="Acme Corp Global", plan="enterprise")
        db.add(tenant)
        await db.flush()

        # Create Demo User
        user = User(
            tenant_id=tenant.id,
            email=demo_email,
            hashed_password=get_password_hash("DemoRecruiter2026!"),
            role="admin"
        )
        db.add(user)
        await db.commit()
        await db.refresh(tenant)

        # Seed sample high-value enterprise engineering documents
        sample_doc_1 = (
            "# Política de Segurança em Nuvem e Resiliência 2026\n\n"
            "Todos os serviços de missão crítica devem operar em arquitetura multi-região ativa-passiva com RTO inferior a 15 minutos e RPO zero. "
            "Os bancos de dados relacionais utilizam PostgreSQL 16 com criptografia AES-256 em repouso e replicação síncrona.\n\n"
            "O controle de acesso exige autenticação multifator (MFA) obrigatória para todos os operadores de produção. "
            "Chaves de API e segredos nunca devem ser armazenados em repositórios Git, sendo auditados pelo EnvGuard CLI e gerenciados via HashiCorp Vault com rotação semanal.\n\n"
            "Em caso de incidentes de segurança de severidade 1, a equipe de DevSecOps deve acionar o procedimento de isolamento de rede em menos de 5 minutos."
        )
        sample_doc_2 = (
            "# Especificação de SLA e Gestão de Filas de Mensageria\n\n"
            "A ingestão de webhooks assíncronos utiliza o PulseQueue com buffer em Redis Streams e garantia de entrega At-Least-Once. "
            "Toda requisição deve conter o cabeçalho 'X-Idempotency-Key' no formato UUIDv7 para evitar duplicação de transações financeiras.\n\n"
            "Quando um endpoint de destino responde com erro HTTP 5xx ou timeout superior a 3000ms, o sistema aplica Exponential Backoff com jitter aleatório (base de 2s, limite de 60s) por no máximo 5 tentativas antes de encaminhar o evento para a Dead-Letter Queue (DLQ).\n\n"
            "O dashboard de monitoramento exibe métricas RED (Rate, Errors, Duration) com alertas automatizados caso a taxa de falhas ultrapasse 0.5%."
        )

        await ingestion_service.process_document(
            db=db,
            tenant_id=tenant.id,
            title="Manual_Seguranca_Cloud_2026.md",
            file_name="Manual_Seguranca_Cloud_2026.md",
            content=sample_doc_1
        )
        await ingestion_service.process_document(
            db=db,
            tenant_id=tenant.id,
            title="Especificacao_SLA_PulseQueue.md",
            file_name="Especificacao_SLA_PulseQueue.md",
            content=sample_doc_2
        )
    else:
        user, tenant = row

    token = create_access_token(subject=user.email, tenant_id=tenant.id, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=60 * 24,
        user_email=user.email,
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        role=user.role
    )

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
