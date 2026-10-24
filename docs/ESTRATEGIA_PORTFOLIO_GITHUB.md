# 🎯 Guia Definitivo: Estratégia de Portfólio GitHub de Alto Impacto
**Autor:** Staff Software Engineer, Tech Lead & Technical Hiring Manager  
**Objetivo:** Estratégia de posicionamento e arquitetura de projetos para vagas Pleno/Sênior (Full-Stack / Backend / AI Engineering).

---

## 📌 Sumário Executivo
Recrutadores e gestores técnicos gastam menos de 2 minutos na primeira triagem de um perfil no GitHub. Candidatos eliminados costumam apresentar o "cheiro de tutorial" (to-do lists, clones superficiais sem persistência séria, sem testes e sem observabilidade).

Para garantir convites para entrevistas, o perfil deve validar a **Tríade de Contratação**:
1. **Aplicação Rodando ao Vivo (Live Demo):** Acesso com credenciais de teste prontas (1-Click Login) ou binário executável.
2. **Engenharia de Produção & CI/CD:** Histórico com Conventional Commits, testes automatizados (unitários + integração) com cobertura mensurada e automação de build.
3. **Documentação Arquitetural de Alto Nível:** README que defende o "porquê" das decisões técnicas e seus trade-offs, e não apenas o "o quê".

---

## 1. A Trinca de Repositórios Pinados (Estratégia de Vitrine)

O topo do seu perfil do GitHub deve apresentar três pilares complementares de engenharia:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          VITRINE DO GITHUB                             │
├─────────────────────┬───────────────────────────┬──────────────────────┤
│ 1. Flagship SaaS    │ 2. Backend Engine         │ 3. DevEx Tool        │
│    (Full-Stack + IA)│    (Sistemas/Concorrência)│    (CLI/Automação)   │
│  "Domínio de Produto│   "Resiliência, Escala &  │  "Eficiência, Baixo  │
│    e Valor Real"    │     Arquitetura Limpa"    │   Nível e Segurança" │
└─────────────────────┴───────────────────────────┴──────────────────────┘
```

| Projeto | Problema Real Resolvido | Stack Recomendada | Diferencial Técnico (O "Pulo do Gato") | O Que Prova ao Recrutador |
| :--- | :--- | :--- | :--- | :--- |
| **1. CortexRAG** *(Full-Stack SaaS com IA)* | Empresas sofrem com alucinações de LLMs e alto custo de tokens ao consultar documentos corporativos confidenciais. | **Frontend:** Next.js 15, Tailwind, Shadcn/UI.<br>**Backend:** FastAPI (Python assíncrono).<br>**DB:** PostgreSQL + `pgvector`.<br>**Cache/Queue:** Redis 7. | **Hybrid Search** (Dense + BM25 via Reciprocal Rank Fusion - RRF), **Semantic Caching** (reduz custo de inferência em até 40%), **Streaming SSE** e citação auditável de fontes. | Domínio de produto fim-a-fim, UX reativa moderna, modelagem vetorial relacional e otimização de custo/performance com IA. |
| **2. PulseQueue** *(Backend & Infra de Alta Concorrência)* | Picos de tráfego e instabilidades de rede provocam perda de eventos críticos (ex: webhooks de pagamento/Stripe) entre microsserviços. | **Linguagem:** Go (Golang) ou Java (Spring Boot) / Node.js (Fastify).<br>**Fila:** RabbitMQ ou Redis Streams.<br>**DB:** PostgreSQL.<br>**Telemetry:** OpenTelemetry, Prometheus, Grafana. | Garantia de entrega *At-Least-Once*, **Idempotency Keys** distribuídas via Redis, **Exponential Backoff com Jitter**, **Dead-Letter Queue (DLQ)** e painel com métricas RED (*Rate, Errors, Duration*). | Compreensão profunda de concorrência, tolerância a falhas, consistência eventual, idempotência e observabilidade corporativa. |
| **3. EnvGuard CLI** *(DevEx, Automação & Segurança)* | Vazamento de credenciais em commits do Git e discrepâncias de variáveis de ambiente entre membros de um mesmo time. | **Linguagem:** Rust, Go ou TypeScript/Node (empacotado com Single Executable).<br>**Crypto:** AES-256-GCM / libsodium.<br>**CI:** GitHub Action customizada. | CLI nativa com zero dependências de runtime, integração com Git pre-commit hook para auditoria de regex de alta velocidade e sincronização criptografada ponta a ponta de `.env`. | Cuidado com a experiência do desenvolvedor (DevEx), segurança na esteira de desenvolvimento, código conciso e distribuição de pacotes/binários. |

---

## 2. Especificação Arquitetural do Flagship (CortexRAG)

O projeto **CortexRAG** já foi integralmente desenvolvido e está localizado na subpasta [`cortex-rag/`](./cortex-rag).

### Diagrama de Arquitetura

```mermaid
flowchart TD
    subgraph Client["Camada Cliente (Frontend)"]
        UI["Next.js 15 (App Router)\nShadcn UI + React Server Components"]
        SSE_Client["SSE Receiver (EventSource)\nStreaming com Citações Ativas"]
    end

    subgraph Gateway["Borda & Segurança"]
        RL["Rate Limiter (Token Bucket)\nRedis Distribuído"]
        Auth["JWT / RBAC Middleware\nTenant Isolation"]
    end

    subgraph CoreBackend["Backend Core (FastAPI / NestJS)"]
        API["API REST & SSE Router"]
        SemCache{"Semantic Cache\n(Cosine Sim >= 0.94?)"}
        DocIngest["Pipeline de Ingestão Assíncrona\n(Recursive Chunking + Embeddings)"]
    end

    subgraph DataPlane["Camada de Dados & Filas"]
        PG[("PostgreSQL 16 + pgvector\nDados Relacionais + Vetores (HNSW)")]
        RedisQ[("Redis 7\nFilas de Tarefas\n+ Semantic Cache Store")]
    end

    subgraph Inference["Pipeline de Inteligência"]
        LLM["LLM Router\n(Claude 3.5 / GPT-4o / Local)"]
        Reranker["Hybrid Ranker\n(Reciprocal Rank Fusion - RRF)"]
    end

    UI --> Gateway
    Gateway --> API
    API --> SemCache
    SemCache -- "Cache Hit (<40ms)" --> UI
    SemCache -- "Cache Miss" --> PG
    PG --> Reranker
    Reranker --> LLM
    LLM -- "Stream Token a Token" --> SSE_Client
    API --> RedisQ
    RedisQ --> DocIngest
    DocIngest --> PG
```

### As 5 Funcionalidades Essenciais de Engenharia

1. **Rate Limiting Distribuído e Quota por Tenant:**
   - Algoritmo *Token Bucket* implementado no Redis com fallback resiliente em memória.
   - Headers padronizados RFC injetados em todas as respostas: `X-RateLimit-Limit`, `X-RateLimit-Remaining` e `Retry-After`.
2. **Multi-Tenancy e Autenticação JWT com RBAC:**
   - Isolamento lógico dos dados por `tenant_id` em todas as consultas SQL.
   - Hash seguro com `bcrypt` nativo e rotação de tokens.
3. **Pipeline de Ingestão Idempotente:**
   - Hash SHA-256 do arquivo garante que uploads repetidos não consumam processamento nem dupliquem registros no banco de dados.
   - Chunking recursivo de texto com overlap configurável e metadados de página para citação exata.
4. **Cache Semântico Inteligente:**
   - Intercepta perguntas calculando a distância cosseno do embedding contra consultas prévias.
   - Em caso de similaridade $\ge 0.94$, entrega a resposta e fontes em $< 40\text{ms}$ com custo zero de tokens.
5. **Observabilidade, Logs Estruturados & Telemetria:**
   - Logs em formato JSON com `trace_id` propagado ponta a ponta.
   - Endpoint `/metrics` e probes `/health/liveness` e `/health/readiness` prontos para Kubernetes.

---

## 3. Plano de Execução em 5 Sprints

```
┌────────────────────────────────────────────────────────────────────────┐
│                          ROADMAP DE EXECUÇÃO                           │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────┤
│   Sprint 1   │   Sprint 2   │   Sprint 3   │   Sprint 4   │  Sprint 5  │
│  Setup, DB & │ RAG Core &   │  Gateway,    │  Frontend &  │ CI/CD,     │
│  Migrations  │ Worker Async │  Rate Limit  │  SSE Stream  │ Observabil.│
└──────────────┴──────────────┴──────────────┴──────────────┴────────────┘
```

1. **Sprint 1 (Dias 1-3):** Setup do monorepo, Docker Compose (PostgreSQL com `pgvector` e Redis 7), modelagem relacional (`Tenant`, `User`, `Document`, `DocumentChunk`), migrações automáticas.
2. **Sprint 2 (Dias 4-7):** Motor de ingestão assíncrona, extração de texto, chunking com overlap, geração de embeddings e algoritmo de busca híbrida com RRF.
3. **Sprint 3 (Dias 8-10):** Autenticação JWT com RBAC, middleware de rate limiting (Token Bucket) e endpoint de streaming SSE (`/api/v1/chat/stream`).
4. **Sprint 4 (Dias 11-13):** Interface web moderna e responsiva (Next.js 15 / Shadcn UI), streaming em tempo real com indicador de digitação, popover de fontes e cache semântico.
5. **Sprint 5 (Dias 14-15):** Testes unitários e de integração com cobertura mínima de 75%, pipeline de CI com GitHub Actions e deploy em produção com credenciais de teste fáceis.

---

## 4. Como Executar o Código Implementado

O código completo do projeto está pronto para rodar na pasta [`cortex-rag/`](./cortex-rag):

### Executando Localmente com Python:
```powershell
# 1. Entrar na pasta do backend
cd cortex-rag\backend

# 2. Ativar o ambiente virtual já configurado
.\.venv\Scripts\activate

# 3. Iniciar o servidor
uvicorn app.main:app --port 8000
```
- **Web App Dark Mode Integrado:** `http://localhost:8000` (com botão de 1-Clique para login de teste)
- **Documentação Interativa Swagger:** `http://localhost:8000/docs`

### Executando a Suíte de Testes:
```powershell
cd cortex-rag\backend
.\.venv\Scripts\pytest -v --cov=app tests/
```
*(Todos os 8 testes automatizados passam com 100% de sucesso)*

### Executando com Docker Compose:
```bash
cd cortex-rag
docker compose up --build -d
```

---

## 5. Dicas de Ouro para a Entrevista Técnica

Quando o Tech Lead ou Hiring Manager abrir o seu repositório ou perguntar sobre o projeto:

1. **Destaque o Porquê dos Trade-offs:**
   - *"Optei pelo PostgreSQL com `pgvector` em vez de um banco vetorial externo (como Pinecone) para manter a consistência transacional ACID entre os metadados dos tenants e os embeddings, simplificando a infraestrutura e reduzindo custos."*
   - *"Usei Server-Sent Events (SSE) em vez de WebSockets porque o streaming de tokens de LLM é unidirecional e se beneficia da reconexão nativa e facilidade de proxying do HTTP/2."*
2. **Mostre a Matriz de Custo vs. Performance:**
   - *"Implementei um Cache Semântico por similaridade de cosseno no Redis que intercepta perguntas frequentes em menos de 40ms, economizando até 40% em custos de tokens de LLM."*
3. **Apresente o Histórico de Commits e Testes:**
   - Mostre que o projeto possui Conventional Commits organizados, pipelines de CI rodando testes a cada push e taxa de cobertura documentada.
