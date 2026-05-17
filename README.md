# TechOnboard — AI-Powered Developer Onboarding Platform

> From day 0 to productive in hours — not weeks.

TechOnboard is an AI-powered technical onboarding platform for engineering teams. It replaces slow, manual onboarding with a fully automated pipeline: a Gemini-powered live interview, GitHub profile analysis, automatic access provisioning, first-ticket assignment, and a personalized day-by-day onboarding plan — all generated without manual intervention.

Built for **Hackathon 2026 · AI Agents Track**.

---

## The Problem

Onboarding a new developer is painful:

| Pain point | Impact |
|---|---|
| **2–4 weeks** before a new hire is truly productive | Lost engineering velocity |
| Manual provisioning of GitHub, Jira, Slack | Days of back-and-forth emails |
| Generic checklists for every seniority level | Poor developer experience |
| No personalization to actual tech stack or gaps | Slow ramp-up |

---

## The Solution

One platform. Five AI agents. Zero manual steps.

```
Manager selects agent & seniority
        │
        ▼
① GitHub Analysis  →  detects real stack & skill gaps
        │
        ▼
② AI Interview     →  Gemini streams live questions via WebSocket
        │
        ▼
③ Auto Provisioning  →  GitHub / Jira / Slack (Lobster Trap policies)
        │
        ▼
④ Ticket Assignment  →  best-fit first Jira ticket from backlog
        │
        ▼
⑤ Personalized Plan  →  Gemini generates a 7-day onboarding plan
```

---

## Example Flow

**Scenario:** Alex, a junior Python developer, joins the backend team.

1. **Manager** selects the Backend AI Agent, sets seniority to _Junior_, and pays 0.50 USDC via x402 on Base Sepolia.
2. **GitHub Analysis** scans Alex's public repos → detects Python ✓, FastAPI ✓, Docker ✗, PostgreSQL ✗.
3. **AI Interview** — Gemini streams real-time questions: _"How comfortable are you with async Python?"_ · _"Have you worked with message queues?"_
4. **Auto Provisioning** — Lobster Trap enforces policies: GitHub READ ✓, Jira Developer role ✓, Slack #backend ✓.
5. **Ticket Assigned** — `BACK-142: Add pagination to /users endpoint` — low complexity, matches Alex's level.
6. **Plan Generated** — Day 1: Env setup · Day 2: Codebase tour · Day 3: Fix a bug · Day 7: Open first PR ✓

---

## Tech Stack

### Frontend
- **React + TypeScript** — SPA
- **Vite** — build tool
- **TailwindCSS** — styling
- **React Router** — routing
- **TanStack Query** — server state
- **WebSocket API** — real-time interview streaming
- **nginx** — static serving + reverse proxy (Railway)

### Backend
- **FastAPI** (Python) — async REST API + WebSocket endpoint
- **LangGraph** — multi-agent orchestration pipeline
- **SQLAlchemy async + asyncpg** — database ORM
- **Pydantic v2** — data validation
- **pgvector** — vector embeddings for RAG

### AI / ML
- **Google Gemini 2.0 Flash** — live interview streaming + plan generation
- **text-embedding-004** — embeddings for RAG codebase indexing
- **LangGraph** — stateful 5-node agent graph

### Infrastructure
- **PostgreSQL + pgvector** — primary database
- **Redis** — caching
- **Docker** (multi-stage build) — containerization
- **nginx + envsubst** — runtime env var substitution
- **Railway** — deployment (4 services: frontend, backend, PostgreSQL, Redis)

### Integrations
- **GitHub API** — public profile & repo analysis
- **Jira API** — ticket retrieval and assignment
- **Slack API** — workspace access provisioning
- **x402 Protocol** — USDC micropayments on Base Sepolia testnet
- **Lobster Trap** — security policy enforcement engine

---

## Architecture

```
Browser (React SPA)
      │  HTTP REST + WebSocket
      ▼
┌─────────────────┐
│  nginx (Railway) │  ← serves static files, proxies /api and /ws
└────────┬────────┘
         │ proxy_pass
         ▼
┌──────────────────────────────────────────────────────┐
│  FastAPI Backend (Railway)                            │
│                                                      │
│  REST API  ─── /api/v1/agents                        │
│             ── /api/v1/onboarding                    │
│             ── /api/v1/payments                      │
│             ── /api/v1/dashboard                     │
│                                                      │
│  WebSocket ─── /ws/interview/{session_id}            │
│                 └─ Gemini 2.0 Flash streaming        │
│                                                      │
│  LangGraph Pipeline                                  │
│   1. analyze_profile   (GitHub API)                  │
│   2. provision_access  (Lobster Trap + integrations) │
│   3. navigate_codebase (RAG over repo)               │
│   4. assign_ticket     (Jira API)                    │
│   5. generate_plan     (Gemini 2.0 Flash)            │
│                                                      │
│  x402 Middleware ── USDC payment verification        │
└───────┬──────────────────────────┬───────────────────┘
        │ asyncpg                  │ redis-py
        ▼                          ▼
┌──────────────┐          ┌──────────────┐
│  PostgreSQL  │          │    Redis     │
│  + pgvector  │          │   (cache)    │
└──────────────┘          └──────────────┘

External APIs: GitHub · Jira · Slack · Base Sepolia (x402)
```

---

## Project Structure

```
techonboard_ia/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py        # LangGraph pipeline
│   │   ├── profile_analyzer.py    # GitHub + Gemini interview
│   │   ├── access_provisioner.py  # GitHub / Jira / Slack provisioning
│   │   ├── codebase_navigator.py  # RAG codebase tour
│   │   └── ticket_assigner.py     # Jira ticket matching
│   ├── api/
│   │   ├── interview.py           # WebSocket endpoint
│   │   ├── onboarding.py          # Session CRUD + plan endpoint
│   │   ├── agents.py              # Agent catalog
│   │   ├── payments.py            # x402 payment routes
│   │   └── dashboard.py           # Manager dashboard
│   ├── models/                    # SQLAlchemy models
│   ├── rag/                       # pgvector indexer + retriever
│   ├── integrations/              # GitHub / Jira / Slack clients
│   ├── payments/                  # x402 handler
│   ├── config.py                  # Pydantic settings
│   └── main.py                    # FastAPI app factory
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Interview.tsx       # Real-time WebSocket chat
│   │   │   ├── OnboardingPlan.tsx  # 7-day plan view
│   │   │   ├── ManagerDashboard.tsx
│   │   │   ├── AgentCatalog.tsx
│   │   │   └── AgentBuilder.tsx
│   │   ├── components/
│   │   │   ├── ChatStream.tsx
│   │   │   ├── PlanTimeline.tsx
│   │   │   └── AccessStatus.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   └── useOnboarding.ts
│   │   └── lib/api.ts             # Axios client
│   ├── nginx.conf                 # nginx template with envsubst
│   └── Dockerfile                 # multi-stage build
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL with pgvector extension
- Redis

### Environment Variables (Backend)

```env
GOOGLE_API_KEY=          # Google Gemini API key
DATABASE_URL=            # postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=               # redis://host:6379/0
GITHUB_TOKEN=            # GitHub personal access token
JIRA_URL=                # https://your-org.atlassian.net
JIRA_EMAIL=
JIRA_API_TOKEN=
SLACK_BOT_TOKEN=
X402_WALLET_ADDRESS=     # USDC receiving wallet (Base Sepolia)
MOCK_MODE=false          # set true to bypass all external APIs
```

### Run locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev          # Vite dev server on :5173
```

### Deploy to Railway

1. Create a Railway project with 4 services: **PostgreSQL**, **Redis**, **backend**, **frontend**.
2. Set `DATABASE_URL` (use `postgresql+asyncpg://` format) and all other env vars on the backend service.
3. Set `BACKEND_URL=https://your-backend.up.railway.app` on the frontend service.
4. Railway auto-builds from the Dockerfiles in each service directory.

---

## Key Features

| Feature | Description |
|---|---|
| **Real-time AI Interview** | Gemini 2.0 Flash streams interview tokens live via WebSocket — no static forms |
| **GitHub Intelligence** | Analyzes public repos to detect real stack, identify gaps, and adapt the plan |
| **Policy-enforced Access** | Lobster Trap enforces security policies before granting any resource access |
| **RAG Codebase Tour** | Indexes the actual project repo and generates a guided walkthrough |
| **x402 Micropayments** | Agents activated via USDC on Base Sepolia using the x402 protocol |
| **Manager Dashboard** | Full visibility: audit logs, session status, cancel/delete controls |
| **Personalized Plan** | 7-day onboarding plan with daily objectives, activities, and deliverables |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/onboarding` | Create a new onboarding session |
| `GET` | `/api/v1/onboarding/{id}` | Get session status |
| `GET` | `/api/v1/onboarding/{id}/plan` | Get generated onboarding plan |
| `PATCH` | `/api/v1/onboarding/{id}/cancel` | Cancel a session |
| `DELETE` | `/api/v1/onboarding/{id}` | Delete a session |
| `GET` | `/api/v1/agents` | List available AI agents |
| `POST` | `/api/v1/agents` | Create a custom agent |
| `POST` | `/api/v1/payments/activate` | Activate agent via x402 payment |
| `GET` | `/api/v1/dashboard/manager` | Manager dashboard data |
| `GET` | `/api/v1/audit-log` | Paginated audit log |
| `WS` | `/ws/interview/{session_id}` | Real-time Gemini interview stream |
| `GET` | `/health` | Health check |

Interactive docs available at `/api/docs` (Swagger UI).

---

## License

MIT
