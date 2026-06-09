# Document Copilot — Implementation Plan

> **Status:** Phases 0–10 complete

## Legend

| Symbol | Meaning |
|--------|---------|
| [ ]    | Not started |
| [x]    | Completed |

---

## Phase 0 — Foundation (Scaffold & Dependencies)

- [x] FastAPI app with health endpoint (`GET /health`)
- [x] pydantic-settings config module
- [x] Vite + React + TypeScript project with Tailwind
- [x] `env.ts`, `supabase.ts`, `http.ts`, `api.ts` lib modules
- [x] Dockerfiles (dev + prod) for backend and frontend
- [x] `docker-compose.yml` + `docker-compose.prod.yml`
- [x] `Makefile` with 15 targets
- [x] `data/download.py` — SEC EDGAR download script

## Phase 1 — Database & Migrations

- [x] 6 SQLAlchemy models (`profiles`, `chat_threads`, `chat_messages`, `message_citations`, `source_documents`, `document_chunks`)
- [x] Alembic setup + initial migration (pgvector, HNSW/GIN indexes, generated tsvector)
- [x] Migration reviewed and ready to apply

## Phase 2 — Auth

- [x] Frontend: Supabase email auth (sign-in, sign-up pages)
- [x] Frontend: `useAuth` hook for session persistence
- [x] Frontend: `ProtectedRoute` redirect component
- [x] Backend: `get_current_user` with Supabase JWT verification via REST API

## Phase 3 — Chat API (Stubbed)

- [x] Backend: `POST /api/chat/stream` SSE endpoint
- [x] Frontend: `@ai-sdk/react` `useChat` integration with streaming
- [x] Chat page with message bubbles, streaming indicator, stop button
- [x] Thread CRUD stubs (`GET/POST /api/threads`, `GET /api/threads/{id}/messages`)

## Phase 4 — Ingestion Pipeline

- [x] `extract.py` — HTML→Markdown via html2text
- [x] `chunk.py` — section-aware chunking with token budget/overlap
- [x] `embed.py` — OpenAI embeddings
- [x] `persist.py` — Supabase storage
- [x] `run.py` — CLI orchestrator
- [x] 5 chunking unit tests passing

## Phase 5 — Retrieval

- [x] `queries.py` — pgvector cosine distance SQL + full-text tsquery SQL
- [x] `fusion.py` — Reciprocal Rank Fusion
- [x] `retriever.py` — `DocumentRetriever` class
- [x] 6 RRF unit tests passing

## Phase 6 — LLM Orchestration (PydanticAI Agent)

- [x] `outputs.py` — `GroundedAnswer`, `Citation`, `SourcePassage` models
- [x] `deps.py` — `DocumentAgentDeps` dataclass
- [x] `agent.py` — PydanticAI agent with `build_agent()` factory
- [x] `instructions.md` — system prompt encoding product contract
- [x] Agent tools: `search_filings`, `read_chunk`
- [x] `orchestrator.py` — full turn lifecycle

## Phase 7 — Grounding & Citation Validation

- [x] `validator.py` — `GroundingValidator` checking citations map to retrieved chunks
- [x] Validation failure → controlled error message
- [x] Insufficient-evidence detection
- [x] 5 unit tests passing

## Phase 8 — Full Integration

- [x] Orchestrator wired into `api/chat.py`
- [x] Streaming: text deltas + citation data parts
- [x] Grounding validation in the chat turn loop

## Phase 9 — Thread Management

- [x] Backend: `thread_repo.py` — list/create/delete/update threads with ownership checks
- [x] Backend: `message_repo.py` — list messages by thread
- [x] Backend: full CRUD endpoints (`GET/POST/PATCH/DELETE /api/threads`, `GET /api/threads/{id}/messages`)
- [x] Ownership verified on every request

## Phase 10 — Error Handling & Edge Cases

- [x] Global exception handlers (422 Pydantic validation, 500 catch-all)
- [x] Chat endpoint validates threadId, messages, and thread ownership
- [x] Grounding failure → "I could not verify the answer" controlled error
- [x] LLM/generic errors → "I encountered an error" message
- [x] All 17 unit tests passing

## Phase 11 — Deployment (Railway)

- [ ] Dockerfiles ready for Railway
- [ ] Supabase production project configured
- [ ] Env vars set in Railway dashboard
- [ ] Smoke test: login → ask question → get cited answer

## Phase 12 — Pilot Polish

- [ ] Onboarding: email auth flow for Driftwood emails only
- [ ] Chat history persistence across sessions
- [ ] Copy/paste citations into analyst reports
- [ ] Mobile browser responsive
- [ ] Performance: <5s end-to-end response
- [ ] Collect pilot feedback
- [ ] Iterate on grounding quality

---

## Key Milestones

| Milestone | Phase | Status |
|-----------|-------|--------|
| `GET /health` returns 200 | 0 | ✅ Done |
| First migration created | 1 | ✅ Done |
| Login UI + JWT verification | 2 | ✅ Done |
| Chat UI streams from backend | 3 | ✅ Done |
| SEC filing data in Supabase | 4 | ✅ Done |
| Hybrid search returns ranked passages | 5 | ✅ Done |
| Agent returns grounded, cited answer | 6 + 7 | ✅ Done |
| End-to-end chat with citations | 8 | ✅ Done |
| Thread management with ownership | 9 | ✅ Done |
| Error handling & edge cases | 10 | ✅ Done |
| Deployed to Railway | 11 | ⏳ Pending |
| Pilot launch (5 analysts) | 12 | ⏳ Pending |

---

## Technical Debt / Non-Goals

- No frontend test suite (per frontend/AGENTS.md)
- No multi-tenant architecture
- No mobile app — responsive browser only
- No external data sources
- No trading recommendations or stock picks
- No separate vector database — Supabase pgvector is the store
