# Nexus

Nexus is an AI-powered UPI transaction analytics platform with a FastAPI backend and a React frontend.

## What The Project Does

- Answers natural-language questions on UPI transaction data.
- Converts user intent to SQL and runs analysis on DuckDB.
- Adds guardrails for unsafe prompts/SQL and rate limits.
- Uses Gemini-based NLU/formatter layers for structured responses.
- Supports chart-ready API output (`bar`, `line`, `pie`) for frontend visualization.
- Includes chat-oriented UX features like voice input and report export.

## Tech Stack

- Backend: Python, FastAPI, DuckDB, Pandas, Gemini API
- Frontend: React + TypeScript (CRA)
- Data: `backend/data/upi_transactions_2024.csv`

## Repository Layout

- `backend/` API, analytics pipeline, NLP, guardrails
- `frontend/` chat UI and visualizations

## Backend Quick Start

1. Create and activate virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Add required keys in `backend/.env`:
   - `GEMINI_API_KEY_PRIMARY`
   - optional fallback keys `GEMINI_API_KEY_FALLBACK_1..4`
4. Start server:
   - `cd backend/src/api`
   - `python server.py`
5. Open:
   - API root: `http://localhost:8000`
   - Docs: `http://localhost:8000/docs`

## Backend Dependency Review (`requirements.txt`)

Runtime imports required for backend startup are present:

- `fastapi`, `uvicorn`, `pydantic`
- `pandas`, `numpy`, `duckdb`, `scipy`
- `google-genai`, `python-dotenv`

No missing core runtime package was found for booting `backend/src/api/server.py`.