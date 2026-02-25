# ACRA AI

Autonomous Code Review Platform with a FastAPI backend and a React dashboard. ACRA analyzes codebases using OpenRouter (Qwen) and surfaces OWASP-focused findings with progress updates over SSE.

**What you get**
- Async review pipeline with chunking, filtering, and persistence
- SSE progress stream for long-running analyses
- Review UI with insights and chat over a codebase

**Requirements**
- Python 3.11+
- Node 18+
- Git (optional, for repo cloning)

## Quick Start (Local)
Backend:
1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `copy .env.example .env` and set `ACRA_OPENROUTER_API_KEY`
5. `cd backend`
6. `alembic -c alembic.ini upgrade head`
7. `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

Frontend:
1. `cd frontend`
2. `npm install`
3. `npm run dev -- --host 127.0.0.1 --port 5173`

Open `http://localhost:5173`.

## Docker
1. `copy .env.example .env` and set `ACRA_OPENROUTER_API_KEY`
2. `docker-compose up --build`

## API Overview
- `POST /api/v1/analyze` start a review
- `GET /api/v1/analyses` list reviews
- `GET /api/v1/analyses/{id}` review details
- `GET /api/v1/analyses/{id}/events` SSE progress stream
- `POST /api/v1/chat` ask about a review

## How It Works
1. Fetch repo (GitHub API or optional git clone)
2. Apply `.gitignore` + binary/lockfile filters
3. Chunk oversized files
4. Analyze with Qwen via OpenRouter
5. Persist results for the UI

## Configuration
Set values in `.env`. This file is ignored by git.

Required:
- `ACRA_OPENROUTER_API_KEY` OpenRouter API key

Common:
- `ACRA_OPENROUTER_MODEL` default `qwen/qwen3-235b-a22b-thinking-2507`
- `ACRA_DATABASE_URL` default `sqlite+aiosqlite:///./acra.db`
- `ACRA_GITHUB_API_BASE` default `https://api.github.com`
- `ACRA_OPENROUTER_API_BASE` default `https://openrouter.ai/api/v1`

Security:
- `ACRA_API_KEY` enables API auth (clients must send `Authorization: Bearer <key>` or `X-ACRA-API-KEY`)
- `ACRA_CORS_ALLOW_ORIGINS` comma-separated list of allowed origins
- `ACRA_RATE_LIMIT_PER_MINUTE` and `ACRA_RATE_LIMIT_WINDOW_S` rate limiting

## Migrations
- Config: `backend/alembic.ini`
- Create: `cd backend && alembic -c alembic.ini revision --autogenerate -m "your message"`
- Apply: `cd backend && alembic -c alembic.ini upgrade head`

## Tests
Run from the repo root:
```
pytest
```

## Notes
- If GitHub API rate limits are hit, supply a token or enable git clone when submitting the review.
- Git clone is optional and must be explicitly enabled in the UI.
