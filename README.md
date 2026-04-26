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
