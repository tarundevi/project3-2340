# NutriBot

A RAG-based nutrition chatbot. Ask natural language questions about nutrition and get evidence-based answers.

## Quick Start (Docker)

```bash
cp .env.example .env   # add your GEMINI_API_KEY
docker compose up --build
```

Open http://localhost — frontend is served by nginx, which proxies `/api` to the backend.

On subsequent runs:

```bash
docker compose up
```

The ChromaDB vector store is persisted via a volume mount at `backend/data/`.

## Manual Setup

### Environment Variables

Copy `.env.example` to `.env` and set your Gemini API key to enable LLM responses. Without it, the bot runs in demo mode with stub responses.

Auth defaults to local email/password accounts for development. To use AWS Cognito instead, set `AUTH_MODE=cognito` and fill in the Cognito environment variables in `.env`.

Conversation persistence also defaults to local SQLite for development. To use AWS-backed persistence, set `PERSISTENCE_MODE=aws` and configure DynamoDB table names plus the S3 bucket/prefix used for conversation snapshots.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Running Tests

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Deployment Notes

### Railway backend

Set these environment variables in Railway:

- `AUTH_MODE`
- `AUTH_JWT_SECRET` for local auth, or the Cognito variables for managed auth
- `PERSISTENCE_MODE`
- `AWS_REGION`
- `DYNAMODB_CONVERSATIONS_TABLE`
- `DYNAMODB_MESSAGES_TABLE`
- `S3_BUCKET_NAME`
- `S3_CONVERSATION_PREFIX`
- `GEMINI_API_KEY`

`backend/railway.toml` only controls build/start; Railway environment variables still need to be configured in the Railway dashboard.

### Vercel frontend

Set `VITE_API_BASE_URL` in Vercel so the frontend points at the deployed backend. The repo now includes [`frontend/vercel.json`](/Users/tarun/workspace/classes/CS2340/project3-2340/frontend/vercel.json) with an SPA rewrite to `index.html`.
