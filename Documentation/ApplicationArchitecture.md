# MuseumSpark — Application Architecture

**Last updated:** 2026-01-15  
**Status:** Living document (derived from the two architecture PDFs; adapted into a single, implementable reference).

## Sources

This document consolidates and de-duplicates content from:

- *MuseumSpark_ Deployment and Architecture Plan.pdf*
- *MuseumSpark_ React + ChatGPT-Powered Trip Planner on Azure.pdf* (historical source; uses older naming)

If these sources diverge, this doc favors the “keep it simple” / hobby-scale approach while calling out optional upgrades.

---

## 1. Purpose and Scope

MuseumSpark is a personal (non-commercial) web application for **ranking, documenting, and planning visits to all museums in the Walker Art Reciprocal Program**.

The Walker Art Reciprocal museum list is extracted from Walker’s published reciprocal membership page (https://walkerart.org/support/membership/reciprocal-membership/) and stored in `data/index/walker-reciprocal.csv`. MuseumSpark uses that list as the authoritative “seed set,” then enriches each museum into a complete record matching the dataset schema and API specification (LLM-assisted + other sources). Walker’s main site is https://walkerart.org/.

In-scope:
- A responsive web UI for browsing/searching the Walker Art Reciprocal museum dataset
- A responsive web UI for saving favorites/visited museums (authenticated)
- Optional trip/itinerary planning features (authenticated)
- A Python API for trip orchestration and persistence
- Server-side AI augmentation (OpenAI API; ChatGPT-class models) for generating/refining trip content
- Member-focused workflows: evaluating trip opportunities and benefits enabled by reciprocal membership
- Hobby-friendly deployment on a single Azure Windows Server VM

Out-of-scope (for the initial architecture):
- High-scale multi-region infrastructure
- Complex microservices decomposition
- Heavy enterprise IAM / SSO

---

## 2. High-Level Architecture

At a high level:

- **Frontend:** React SPA (Vite) + Tailwind CSS
- **Backend:** FastAPI (Python) served via Uvicorn
- **AI integration:** PydanticAI agents calling the OpenAI API
- **Data:** Walker Art Reciprocal museum dataset stored as JSON (authoritative) with a derived search/index
- **Database:** SQLite (single-file DB) for user accounts + personalization (+ optional trips)
- **Hosting:** Single Azure Windows Server VM (self-hosted)

### 2.1 System Context

Users access a single origin (domain/host). The SPA makes HTTP requests to the backend API. The backend reads/writes SQLite and makes on-demand calls to the OpenAI API.

### 2.2 Component Diagram (Mermaid)

```mermaid
flowchart LR
  U[User Browser] -->|HTTPS| W[Single Origin
(IIS/Nginx or FastAPI Static)]

  W -->|serves| SPA[React SPA
(Vite build)]
  U -->|/api/v1/*| API[FastAPI Backend
(Uvicorn)]

  API --> DATA[(Museum Dataset
JSON + index)]
  API --> DB[(SQLite
user/trip DB)]
  API -->|API calls| OAI[OpenAI API
ChatGPT-class models]

  subgraph Azure Windows VM
    W
    SPA
    API
    DATA
    DB
  end
```

Notes:
- A common simplification is to serve the SPA and the API from the same FastAPI process (static files + API routes), avoiding CORS.
- If you use IIS (or another web server) to serve static assets, it typically reverse-proxies `/api/v1/*` to the FastAPI service.

---

## 3. Frontend Architecture (React)

### 3.1 Responsibilities

- Authentication UI (login/register)
- Trip management flows (create trip, edit trip, view itinerary)
- Calls backend endpoints for:
  - user/trip CRUD
  - AI-triggered generation (e.g., draft itinerary, refine itinerary)

### 3.2 Technology

- React
- Vite build toolchain
- Tailwind CSS (v4 referenced in source material)
- React Router (typical for SPA routing)

### 3.3 Deployment Output

- Production build output is a static folder (e.g., `dist/`)
- SPA routing requires a fallback to `index.html` for unknown non-API routes

---

## 4. Backend Architecture (FastAPI)

### 4.1 Responsibilities

- Provides a REST-ish HTTP API for:
  - authentication
  - trip CRUD
  - itinerary generation/refinement triggers
- Encapsulates OpenAI calls (do not call OpenAI directly from the browser)
- Reads/writes SQLite
- Enforces input/output validation (Pydantic models)

### 4.2 AI Integration (PydanticAI + OpenAI)

The architecture uses PydanticAI agents to:
- Define **structured outputs** (Pydantic models) for AI responses
- Validate model output and handle validation failures
- Keep prompt/tooling logic in Python, close to the domain models

Recommended patterns:
- Define a small set of domain output models (e.g., `City`, `Attraction`, `ItineraryDay`, `ItineraryItem`)
- Prefer structured JSON-like outputs over free-form text
- Keep “prompt templates” versioned and testable

### 4.3 Concurrency and Latency

- AI calls can be slow; use async endpoints (`async def`) and async OpenAI clients.
- SQLite is fine at hobby scale, but heavy concurrent writes can be a bottleneck. If this becomes a problem, upgrading the DB is the first lever.

---

## 5. Data Architecture

## 5.0 Dataset Workflow (Authoritative)

The MuseumSpark dataset is built from the Walker Art Reciprocal roster and progresses through these stages:

1) **Validate the Walker reciprocal roster**
  - Input: `data/index/walker-reciprocal.csv`
  - Goal: ensure the seed list is structurally sound (headers, URLs, duplicates/artifacts)
  - Script: `python scripts/validate-walker-reciprocal-csv.py`

2) **Add all museums to `data/index/all-museums.json` (master list for the app)**
  - Goal: every reciprocal museum appears in the master list, even if only partially populated initially
  - This file is what the app uses for browsing/search.
  - In practice, this is achieved by ingesting the roster into `data/states/*.json` and rebuilding the index via `scripts/build-index.py`.

3) **Add museums by state to `data/states/{state}.json`**
  - Goal: create a per-state working file for curation/enrichment
  - Over time, each state file is updated until records meet the dataset schema and quality standards.

Automated ingest helper:
- `python scripts/ingest-walker-reciprocal.py --rebuild-index`

After state files are enriched, the index/master list can be rebuilt to keep `all-museums.json` in sync with the curated per-state records.

### 5.1 Museum Dataset (Authoritative)

The museum dataset is the system’s “single source of truth”:

- `data/states/*.json` (canonical records)
- `data/schema/museum.schema.json` (validation rules)
- `scripts/validate-json.py` / `scripts/validate-json.ps1` (quality gates)

The initial museum roster comes from Walker’s reciprocal membership list:

- Seed input: `data/index/walker-reciprocal.csv`
- Build/enrichment pipeline: derive canonical museum records matching the schema, then generate derived indices for search and browsing.

For serving/search performance, the backend can read from a pre-built index (e.g., `data/index/all-museums.json`) or load a denormalized copy into SQLite.

### 5.2 Application Database (SQLite)

#### Why SQLite

- Lowest operational overhead: single file, no DB server
- Easy backups (copy the file)
- Sufficient for low-traffic / single-VM deployments

#### Suggested core tables (logical)

These are representative entities inferred from the architecture documents and the feature spec:
- `users`
- `favorites` / `visited` (join tables between users and museums)
- Optional `trips` (owner, title, dates, metadata)
- Optional `itinerary_items` (day, time, museum_id, notes, generated content)
- Optional: `ai_runs` (prompt versions, model, cost estimates, timestamps)

If you denormalize museum data into SQLite for query speed, treat that as a derived cache from the canonical JSON dataset (rebuildable).

---

## 6. API Surface (Conceptual)

The PDFs describe endpoints for authentication and trip management, plus AI-triggered generation.

This repo contains the canonical API specification in `Documentation/MuseumAPI.md`. It covers:
- museum browsing/search/filtering
- user personalization (accounts, favorites, visited)
- optional trip/itinerary management
- admin/curation endpoints for dataset maintenance

This architecture document does not attempt to lock the API contract, but it assumes:
- `/api/v1/auth/*` endpoints for login/register
- `/api/v1/museums/*` endpoints for museum browsing
- `/api/v1/trips/*` endpoints for trip management
- `/api/v1/*` AI-trigger endpoints (e.g., generate/refine itinerary)

---

## 7. Deployment Architecture (Azure Windows Server VM)

### 7.1 Deployment Goals

- One VM, minimal moving parts
- Easy manual operations (RDP + PowerShell)
- Optionally automated with lightweight CI/CD

### 7.2 Network and Ports

- Azure NSG: open inbound ports as needed
  - `80` (HTTP) and/or `443` (HTTPS)
  - optionally `8000` for direct Uvicorn during early testing (not ideal long-term)
- Windows Firewall: mirror the same allowed inbound ports

### 7.3 Serving Options

**Option A (simplest): Serve SPA via FastAPI**
- FastAPI serves static `dist/` assets
- API routes mounted under `/api/v1/*`
- Unknown routes fallback to `index.html` so React Router works
- Same origin avoids CORS complexity

**Option B: IIS serves SPA + reverse proxies API**
- IIS serves static files from the build output folder
- IIS reverse-proxies `/api/v1/*` to Uvicorn/FastAPI running on localhost (e.g., `127.0.0.1:8000`)
- Requires IIS reverse proxy configuration (ARR or equivalent)

### 7.4 Running the Backend as a Service

For persistence across reboots and logouts:
- Run Uvicorn as a Windows Service using **NSSM** (Non-Sucking Service Manager)
- Configure:
  - working directory
  - environment variables
  - restart on failure

### 7.5 Secrets Management

- Set `OPENAI_API_KEY` as an environment variable on the VM
- Do not store secrets in source control
- Prefer machine/user env vars or a `.env` file excluded by `.gitignore`

### 7.6 TLS / HTTPS

- For a custom domain, point an A record at the VM public IP
- Terminate TLS at IIS (or another front web server)
- If using Let’s Encrypt on Windows, automate renewal (exact tooling choice is implementation-specific)

---

## 8. Security Considerations (Hobby-Scale, Sensible Defaults)

### 8.1 Authentication

- Implement lightweight account support (small set of users)
- Store only **hashed** passwords (bcrypt/Argon2 via a well-known library)
- Consider JWT access tokens (or cookie-based sessions) depending on UI needs

### 8.2 Input Validation

- Use Pydantic models for request bodies
- Parameterize SQL queries (or use an ORM) to avoid SQL injection

### 8.3 AI Safety and Abuse Controls

- Rate-limit or throttle AI endpoints
- Add basic request auditing for AI-trigger endpoints
- Treat AI outputs as untrusted until validated by schema

---

## 9. Observability and Operations

### 9.1 Logging

- Capture Uvicorn/FastAPI logs to files (with rotation)
- Log AI request metadata (timestamps, model used, success/failure) without storing sensitive user content unnecessarily

### 9.2 Backups

- Schedule periodic backups of:
  - SQLite DB file
  - any user-uploaded content (if introduced)
  - configuration and deployment scripts

A simple approach is a nightly copy to off-VM storage.

---

## 10. CI/CD (Optional)

A minimal pipeline can:
- build the frontend
- run backend unit checks/tests
- copy artifacts to the VM
- restart the backend service

GitHub Actions is explicitly mentioned as a reasonable hobby-scale option.

---

## 11. Key Tradeoffs and Upgrade Path

### 11.1 Current Tradeoffs

- **Single VM** is simple, but is also a single point of failure
- **SQLite** is easy, but limited under write-heavy concurrency
- **AI calls** add latency and cost; caching and limits matter

### 11.2 Upgrade Path (when needed)

If the project grows, typical next steps are:
- move SQLite → PostgreSQL
- add a reverse proxy and proper TLS termination if not already done
- containerize (Docker) for repeatable deployments
- move from VM hosting to managed services (optional)

---

## 12. Implementation Notes for This Repository

This repository currently contains dataset and scripting assets (e.g., JSON files under `data/` and validation scripts under `scripts/`). As the web application code is added (frontend/backend), align it to this architecture and keep this document updated when decisions change.
