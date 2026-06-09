# Document Copilot

Research-assistant chatbot for SEC filings. Ask natural-language questions about 10-Ks, 10-Qs, and other financial documents — get grounded answers with cited source passages.

## Purpose

**Document Copilot turns hours of document reading into seconds of Q&A.**

Financial professionals spend enormous time reading through SEC filings — hundreds of pages per filing, dozens of filings per quarter. The information is all public, all structured, but the sheer volume makes it impractical to search manually. Document Copilot ingests these filings and lets you ask questions in plain English, returning concise answers with citations back to the exact source passage.

The key design principle: **every answer is grounded in retrieved evidence**. The system does not allow the LLM to fabricate information. If a citation can't be verified against the actual document corpus, the answer is rejected.

## Use Cases

| Who | What they can do |
|-----|------------------|
| **Equity Research Analyst** | "Compare Apple's gross margin trajectory from 2022 to 2025 and explain the drivers." |
| **Portfolio Manager** | "Which of my covered companies mentioned AI as a risk factor in their most recent 10-K?" |
| **Compliance Officer** | "Show me all disclosure controls and procedures descriptions across our portfolio." |
| **Investment Banker** | "Find precedent transactions in the semiconductor space from 2023-2025 filings." |
| **Data Scientist** | "Extract all revenue figures by segment for FAANG companies over the last 3 years." |
| **Journalist** | "What did Microsoft say about OpenAI investment risks in their 2025 10-K?" |
| **Law Student** | "Walk me through the risk factor section of NVDA's latest filing compared to AMD's." |

## How It Works (End-to-End)

```
                         ┌─────────────────────────────────────────────────────────┐
                         │                     YOUR QUESTION                       │
                         │        "What was Apple's Services revenue in 2025?"      │
                         └────────────────────────┬────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        1.  INGESTION (done ahead of time)                         │
│                                                                                   │
│   SEC EDGAR ──▶ download.py ──▶ chunking (500t) ──▶ embedding ──▶ pgvector DB     │
│                                                                                   │
│   Each filing is split into overlapping passages, each passage gets an embedding  │
│   vector, and both the vector and full text are stored in Postgres for retrieval. │
└──────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        2.  RETRIEVAL (hybrid search)                              │
│                                                                                   │
│   ┌─── Your question ───┐                                                        │
│   │                     │                                                         │
│   │   Embed question    │                                                         │
│   │   with same model   │                                                         │
│   └────────┬────────────┘                                                         │
│            │                                                                      │
│   ┌────────▼────────┐          ┌───────────────────┐                             │
│   │  SEMANTIC SEARCH │          │  FULL-TEXT SEARCH  │                             │
│   │  (pgvector)      │          │  (Postgres tsquery)│                             │
│   │  "Services       │          │  "services AND     │                             │
│   │   revenue 2025"  │          │   revenue AND 2025"│                             │
│   └────────┬────────┘          └──────────┬─────────┘                             │
│            │                              │                                       │
│            └──────────┬───────────────────┘                                       │
│                       │                                                            │
│               ┌───────▼────────┐                                                   │
│               │  RRF FUSION    │                                                   │
│               │  (Reciprocal   │                                                   │
│               │   Rank Fusion) │                                                   │
│               └───────┬────────┘                                                   │
│                       │                                                            │
│                       ▼                                                            │
│              Top-10 ranked passages                                                 │
│              (with scores from both methods)                                       │
│                                                                                   │
│   Why hybrid? Semantic search catches synonyms and paraphrases ("Services          │
│   segment performance"), full-text guarantees keyword precision ("Services         │
│   revenue 2025"). RRF merges both rankings into one robust result set.             │
└──────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        3.  GENERATION (LLM with tools)                            │
│                                                                                   │
│   ┌──────────────────────────────────────────────────────────────────────┐        │
│   │  SYSTEM: You are a research assistant. You have access to the       │        │
│   │  search_filings tool. You MUST cite every claim with [1], [2] etc. │        │
│   │  Each citation must reference a real chunk_id from search results.  │        │
│   └──────────────────────────────────────────────────────────────────────┘        │
│                                                                                   │
│   LLM (Claude / GPT / Gemini / Grok / ...)                                        │
│      │                                                                           │
│      ├── 1. Calls search_filings("Services revenue 2025 Apple")                  │
│      │      ◀── Receives top passages with chunk_id + content                     │
│      │                                                                           │
│      ├── 2. Calls read_chunk(chunk_id) if it needs the full passage              │
│      │                                                                           │
│      └── 3. Generates grounded answer with citations                             │
│                                                                                   │
│   Example output:                                                                 │
│                                                                                   │
│     "Apple's Services revenue reached $25.1B in Q1 2025, up 14% YoY, driven      │
│      by record App Store and Apple Music performance [1][2]. The Services         │
│      segment now represents 24% of total revenue, up from 20% in 2023 [3]."       │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        4.  GROUNDING VALIDATION                                   │
│                                                                                   │
│   Every [1], [2], [3] is checked:                                                 │
│                                                                                   │
│   ✓ Citation [1] → chunk_id matches a retrieved passage                           │
│   ✓ Citation [2] → chunk_id matches a retrieved passage                           │
│   ✓ Citation [3] → chunk_id matches a retrieved passage                           │
│                                                                                   │
│   If ANY citation doesn't match a real chunk → answer REJECTED                    │
│   If NO citations present at all → answer REJECTED                                │
│   If too few citations for answer length → answer REJECTED                        │
│                                                                                   │
│   Rejected answers trigger a re-prompt: "You must cite the source passages."      │
│                                                                                   │
│   This prevents hallucination. The LLM cannot invent facts — they must come       │
│   from the actual document corpus.                                                │
└──────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        5.  STREAMING (to the frontend)                            │
│                                                                                   │
│   ┌────────────┐         ┌──────────────────┐         ┌──────────────────┐       │
│   │  FastAPI   │ ──SSE──▶│  React Frontend  │ ──JWT──▶│  Supabase Auth   │       │
│   │  Backend   │   stream│  (Vite + TS)     │   auth  │  (email/pw)      │       │
│   └────────────┘         └──────────────────┘         └──────────────────┘       │
│        │                                                                          │
│        ├── "0:" = text chunk (streaming incremental text)                        │
│        └── "2:" = citations JSON (final citations with chunk_id + excerpt)       │
│                                                                                   │
│   The frontend renders text as it arrives (low latency), then appends             │
│   clickable citation badges at the end. Each badge links to the source doc.      │
└──────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
                         ┌─────────────────────────────────────────┐
                         │         YOU SEE ON SCREEN:               │
                         │                                           │
                         │  Q: What was Apple's Services revenue     │
                         │     in 2025?                              │
                         │                                           │
                         │  A: Apple's Services revenue reached      │
                         │  $25.1B in Q1 2025, up 14% YoY, driven   │
                         │  by record App Store and Apple Music      │
                         │  performance [1][2]. The Services segment │
                         │  now represents 24% of total revenue [3]. │
                         │                                           │
                         │  ┌──────┐ ┌──────┐ ┌──────┐              │
                         │  │ [1] │ │ [2] │ │ [3] │  ← clickable    │
                         │  └──────┘ └──────┘ └──────┘              │
                         │                                           │
                         │  [1] AAPL 10-K 2025-10-31 — "Management   │
                         │  Discussion" — "Services revenue grew     │
                         │  14% to $25.1B in the first quarter..."   │
                         └─────────────────────────────────────────┘
```

### Key design decisions

**LLM and embeddings are decoupled.** You can use any combination:

```env
# Powerful reasoning LLM + cheap/efficient embedding provider
LLM_PROVIDER=anthropic          # Claude Sonnet 4
EMBEDDING_PROVIDER=openai       # text-embedding-3-small
```

```env
# Fully local (no API keys needed)
LLM_PROVIDER=ollama              # Llama 3.2 via Ollama
EMBEDDING_PROVIDER=ollama        # nomic-embed-text via Ollama
```

```env
# Same provider for both
LLM_PROVIDER=gemini              # Gemini 2.0 Flash
EMBEDDING_PROVIDER=gemini        # gemini-embedding-001
```

```env
# Open-source LLM via OpenRouter + Gemini embeddings
LLM_PROVIDER=openrouter          # Any OpenRouter model
EMBEDDING_PROVIDER=gemini        # gemini-embedding-001
```

```env
# Free local LLM + cloud embeddings
LLM_PROVIDER=lm_studio           # Local model via LM Studio
EMBEDDING_PROVIDER=cohere        # embed-english-v3.0
```

## Features

- **📄 SEC Filing Ingestion** — Download, chunk, embed, and index filings from SEC EDGAR
- **🔍 Hybrid Retrieval** — Semantic (pgvector) + full-text (Postgres tsvector) search fused via Reciprocal Rank Fusion
- **💬 Grounded Q&A** — LLM answers must cite retrieved source chunks; answers without citations are rejected
- **🔗 Source Citations** — Every claim links back to the exact passage, with ticker, filing date, and document metadata
- **🔐 Supabase Auth** — Email-based authentication with JWT bearer tokens
- **💾 Chat History** — Threaded conversations persisted in Postgres
- **⚡ Streaming Responses** — Server-Sent Events with AI SDK data parts for text + citations

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend   │────▶│     Backend      │────▶│    Database     │
│  React SPA   │     │   FastAPI +      │     │  Postgres +     │
│  Vite + TS   │     │   PydanticAI     │     │  pgvector       │
│  Tailwind v4 │◀────│                  │◀────│                 │
└──────────────┘     └──────────────────┘     └─────────────────┘
       │                     │                        │
       │                     │                        ├─ document_chunks
       │                     │                        │  (vectors + full-text)
       │                     │                        ├─ threads
       │                     │                        └─ messages
       │                     │
       │                     ├── Assistant Agent (PydanticAI)
       │                     │   ├── search_filings tool
       │                     │   ├── read_chunk tool
       │                     │   └── GroundedAnswer output
       │                     │
       │                     ├── Retrieval Pipeline
       │                     │   ├── Semantic search (pgvector)
       │                     │   ├── Full-text search (Postgres)
       │                     │   └── RRF fusion
       │                     │
       │                     ├── Grounding Validator
       │                     └── Embedding Provider (15 options)
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.12+, FastAPI, PydanticAI | API server, agent orchestration |
| **Frontend** | React 19, TypeScript, Vite, Tailwind v4 | SPA user interface |
| **Database** | PostgreSQL 17 + pgvector | Relational storage + vector search |
| **Auth** | Supabase Auth (email/password) | Authentication + JWT |
| **LLM** | 14 providers via PydanticAI | Answer generation |
| **Embeddings** | 15 providers | Document vectorization |
| **Orchestration** | uv (packaging), pnpm (frontend), Docker | Dev & deployment tooling |

## LLM Providers

| Provider | Env Name | Embedding Support | Type |
|----------|----------|-------------------|------|
| OpenAI | `openai` | ✅ | Native |
| Gemini | `gemini` | ✅ | Native |
| Anthropic | `anthropic` | ❌ | Native |
| Groq | `groq` | ❌ | Native |
| Mistral | `mistral` | ✅ | Native |
| Cohere | `cohere` | ✅ | Native |
| xAI (Grok) | `xai` | ❌ | Native |
| Cerebras | `cerebras` | ❌ | Native |
| AWS Bedrock | `bedrock` | ✅ | Native |
| OpenRouter | `openrouter` | ✅ | OpenAI-compat |
| NVIDIA | `nvidia` | ✅ | OpenAI-compat |
| Ollama | `ollama` | ✅ | OpenAI-compat |
| LM Studio | `lm_studio` | ✅ | OpenAI-compat |
| HuggingFace | `huggingface` | ✅ | OpenAI-compat |

## Embedding Providers

| Provider | Env Name | Dimensions | Approach |
|----------|----------|------------|----------|
| OpenAI | `openai` | 1536–3072 | Native SDK |
| Gemini | `gemini` | 768–3072 | Native SDK |
| Cohere | `cohere` | 1024+ | Native SDK |
| VoyageAI | `voyageai` | 768–1024 | Native SDK |
| Sentence-Transformers | `sentence_transformers` | 384+ | Local model |
| AWS Bedrock | `bedrock` | 1024+ | Boto3 |
| HuggingFace | `huggingface` | 384–4096 | OpenAI-compat |
| OpenRouter | `openrouter` | 1536–4096 | OpenAI-compat |
| NVIDIA | `nvidia` | 1024–4096 | OpenAI-compat |
| Ollama | `ollama` | 384–4096 | OpenAI-compat |
| LM Studio | `lm_studio` | varies | OpenAI-compat |
| Mistral | `mistral` | 1024 | Native SDK |
| Together AI | `together` | 768–1024 | OpenAI-compat |
| Fireworks AI | `fireworks` | 768–4096 | OpenAI-compat |
| Perplexity | `perplexity` | 1024–2560 | Base64-decode |

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 22+
- pnpm 11.5+
- Docker Desktop (for local Postgres)
- A Supabase project (free tier)

### 1. Clone and configure

```bash
git clone <repo-url> && cd document-copilot

# Copy environment and edit with your keys
cp .env.example .env
```

Required config in `.env`:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Pick your LLM + embedding provider (e.g. Gemini with Gemini embeddings):

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
EMBEDDING_PROVIDER=gemini
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

### 2. Start the database

```bash
docker compose up -d db
```

### 3. Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Health check: `GET /health`.

### 4. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

The app is available at `http://localhost:5173`.

### 5. Ingest documents

Download SEC filings:

```bash
uv run python data/download.py
```

This downloads 10-Ks for AAPL, MSFT, NVDA, AMZN, GOOGL, and more into `data/payloads/`.

Ingest a filing:

```bash
uv run python backend/ingest/ingest.py --dir data/payloads/AAPL_2025-10-31
```

### 6. Run tests

```bash
cd backend
uv run pytest tests/ -v
```

## Docker Development

Start all three services (db, backend, frontend):

```bash
docker compose up --build
```

- Postgres: `localhost:5432`
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Production Deployment

### Backend (Railway, Fly.io, etc.)

```dockerfile
# backend/Dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Required environment variables:**

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `DATABASE_URL` | Postgres connection string |
| `LLM_PROVIDER` | LLM provider name |
| `GEMINI_API_KEY` (or your provider's key) | LLM API key |
| `EMBEDDING_PROVIDER` | Embedding provider (optional, defaults to LLM) |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) |

### Frontend (Vercel, Railway, etc.)

```dockerfile
# frontend/Dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml .npmrc ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
CMD ["nginx", "-g", "daemon off;"]
```

The nginx config proxies `/api/` requests to the backend service:

```nginx
location /api/ {
    proxy_pass http://backend:8000;
}
```

**Required environment variables:**

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key |
| `VITE_API_BASE_URL` | Backend API URL |

### Supabase Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Enable email auth in Authentication → Settings
3. Run the database migrations:

```bash
cd backend
uv run alembic upgrade head
```

Supabase is used **only for authentication**. All document and chat data lives in your own Postgres database.

## Project Structure

```
document-copilot/
├── .env                        # Local configuration
├── .env.example                # Documented config template
├── docker-compose.yml          # Dev environment (db + backend + frontend)
├── data/
│   ├── download.py             # SEC EDGAR filing downloader
│   └── payloads/               # Downloaded filings (gitignored)
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint
│   │   ├── config.py           # Pydantic settings (all env vars)
│   │   ├── embeddings.py       # 15 embedding provider implementations
│   │   ├── api/chat.py         # Chat REST endpoints
│   │   ├── assistant/
│   │   │   ├── agent.py        # PydanticAI agent factory (14 LLMs)
│   │   │   ├── deps.py         # Agent dependencies
│   │   │   ├── outputs.py      # GroundedAnswer + Citation models
│   │   │   └── instructions.md # System prompt
│   │   ├── auth/               # Supabase JWT verification
│   │   ├── chat/orchestrator.py# Retrieval → LLM → grounding → stream
│   │   ├── database/           # SQLAlchemy models, connection, repos
│   │   ├── grounding/          # Citation validation
│   │   ├── retrieval/          # pgvector + full-text + RRF fusion
│   │   └── prompts/            # Prompt templates
│   ├── ingest/                 # Ingestion scripts (Markdown → chunks → embed → DB)
│   ├── tests/                  # 17 unit tests
│   ├── Dockerfile.dev
│   ├── pyproject.toml
│   └── AGENTS.md
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Router
│   │   ├── main.tsx            # Entry point
│   │   ├── components/         # React components
│   │   ├── pages/              # Route-level pages
│   │   ├── hooks/              # Custom hooks
│   │   └── lib/                # API client, auth, env config
│   ├── Dockerfile              # Production (nginx)
│   ├── Dockerfile.dev
│   ├── nginx.conf
│   ├── vite.config.ts
│   └── AGENTS.md
└── AGENTS.md                   # Agent instructions for codegen tools
```

## API Reference

### `GET /health`
Returns `{"status": "ok"}`.

### `POST /api/chat/stream`
Stream a chat turn. Requires Supabase JWT in `Authorization: Bearer <token>`.

**Request:**
```json
{
  "threadId": "uuid",
  "messages": [{"role": "user", "content": "What was Apple's revenue in 2025?"}]
}
```

**Response:** Server-Sent Events stream:
- `0:{text_chunk}` — streaming text
- `2:{citations_json}` — final citations with chunk IDs and excerpts

### Threads API (all require auth)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/threads` | List user's threads |
| `POST` | `/api/threads` | Create new thread |
| `GET` | `/api/threads/{id}` | Get thread details |
| `PATCH` | `/api/threads/{id}` | Update thread title |
| `DELETE` | `/api/threads/{id}` | Delete thread + messages |
| `GET` | `/api/threads/{id}/messages` | List messages in thread |

## Answers are Grounded

Every answer must cite the specific source passage it came from. The system:

1. **Retrieves** relevant chunks via hybrid search (semantic + full-text + RRF)
2. **Generates** an answer with citations using the LLM
3. **Validates** every citation maps to a retrieved chunk
4. **Rejects** ungrounded claims — the LLM is re-prompted if citations are missing or fabricated

Citations link to the exact chunk with ticker, filing type, filing date, and a direct excerpt.
