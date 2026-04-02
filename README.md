# NutriBot

A RAG-based nutrition chatbot. Ask natural language questions about nutrition and get evidence-based answers.

## Setup

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

### Environment Variables (optional)

Copy `.env.example` to `.env` and set your Gemini API key to enable LLM responses. Without it, the bot runs in demo mode with stub responses.

## Running Tests

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```
