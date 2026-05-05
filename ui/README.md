# Multi-RAG AI Assistant

This project implements a **Multi-Agent Retrieval-Augmented Generation (Multi-RAG)** system using a local LLM stack.

The application consists of:

- multiple domain-specific AI agents (HR, LOTR, Harry Potter, etc.)
- per-agent knowledge bases and vector indexes
- a backend (FastAPI)
- a frontend (React)

---

## Project Overview

Each agent has:

- its own documents (`api/data/<agent>/`)
- its own FAISS vector index (`api/indexes/<agent>/`)
- its own retrieval pipeline

The system performs:

1. Retrieval (top-k chunks)
2. Prompt construction
3. Answer generation via local LLM (Ollama)

---

## Key Features

- Multi-agent architecture (specialists + supervisor)
- Per-agent RAG (separate indexes)
- Semantic retrieval (embeddings)
- FAISS vector search
- Offline ingest pipeline
- Debug metadata (ETAP 8)
- React UI
- Fully local execution

---

# Getting Started (Frontend)

This frontend was bootstrapped with Create React App.

## Available Scripts (Frontend)

In the `ui/` directory, you can run:

### `npm start`

Runs the frontend in development mode.  
Open http://localhost:3000 to view it in your browser.

The page will reload when you make changes.  
You may also see any lint errors in the console.

---

### `npm test`

Launches the test runner in the interactive watch mode.

---

### `npm run build`

Builds the app for production to the `build` folder.

The build is optimized and minified.

---

### `npm run eject`

**Note: this is a one-way operation.**

This exposes full configuration (webpack, babel, etc.).

---

# Backend (FastAPI)

## Available Scripts (Backend)

In the `api/` directory:

### `uv run uvicorn main:app --reload`

Runs backend API in development mode.

Available at:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs

---

### `uv run python -m retrieval.ingest --all`

Builds FAISS indexes for all agents.

Required before first use.

---

### `uv run python -m retrieval.ingest --agent hr`

Builds index for a single agent.

---

# Full Setup (Step-by-step)

## 1. Clone repository
git clone https://github.com/agorkaissi/diplomaProject.git

cd diplomaProject


---

## 2. Install backend

uv sync


---

## 3. Install frontend


cd ui
npm install


---

## 4. Setup Ollama (LLM)

Download: https://ollama.com/download

Then run:

ollama pull llama3.2:1b


---

## 5. Build indexes (REQUIRED)

cd api
uv run python -m retrieval.ingest --all


---

## 6. Run application

### Terminal 1 (backend)


cd api
uv run uvicorn main:app --reload


### Terminal 2 (frontend)

cd ui
npm start


---

# API Example

POST `/chat`

{
"question": "How many days of holiday does each worker have?",
"selected_agent": "hr"
}


---

# Debug Metadata (ETAP 8)

Each response includes debug data:

{
"agent": "hr",
"answer": "...",
"sources": [...],
"debug": {
"agent_type": "specialist",
"retrieval_time_ms": ...,
"generation_time_ms": ...,
"confidence": ...,
"chunks": [...]
    }
}


---

# Notes

- Retrieval is done per agent (Multi-RAG)
- Each agent has its own FAISS index
- Debug layer allows RAG analysis
- System works fully locally (no API calls)

---

# Limitations

- Small LLM (llama3.2:1b)
- No reranking yet
- No semantic routing
- Confidence is heuristic

---

# Future Improvements

- semantic routing
- hybrid retrieval (BM25 + embeddings)
- reranking layer
- evaluation pipeline
- multi-agent comparison

---
# Project Structure

```text
diplomaProject/
├── api/
│   ├── data/                 # source documents for agents
│   │   ├── hogwart/
│   │   ├── hr/
│   │   ├── lotr/
│   │   └── PanTadeusz/
│   │
│   ├── indexes/              # FAISS indexes generated during ingest
│   │   ├── hr/
│   │   ├── harrypotter/
│   │   ├── frodo/
│   │   └── ksrobak/
│   │
│   ├── prompts/              # prompt builders
│   │   ├── __init__.py
│   │   └── builders.py
│   │
│   ├── retrieval/            # RAG pipeline
│   │   ├── __init__.py
│   │   ├── chunking.py       # document chunking
│   │   ├── embeddings.py     # embedding model
│   │   ├── ingest.py         # offline indexing
│   │   ├── retriever.py      # query-time retrieval
│   │   ├── types.py          # retrieval data types
│   │   └── vector_store.py   # FAISS vector store
│   │
│   ├── agents.db             # SQLite database
│   ├── db.py                 # database configuration
│   ├── main.py               # FastAPI entry point
│   ├── models.py             # SQLAlchemy models
│   ├── ollama_client.py      # Ollama client
│   ├── router.py             # agent routing
│   ├── runtime.py            # Multi-RAG orchestration
│   ├── schemas.py            # API schemas
│   └── test_main.http        # HTTP test requests
│
├── ui/
│   ├── public/
│   └── src/
│       ├── pages/
│       │   ├── dashboard/
│       │   ├── AiAssistant.js # main chat UI with RAG debug
│       │   ├── Dashboard.js
│       │   ├── Home.js
│       │   └── Scenarios.js
│       │
│       ├── App.css
│       ├── App.js
│       ├── index.css
│       ├── index.js
│       ├── Layout.js
│       └── router.js
│
├── pyproject.toml            # Python dependencies
├── uv.lock                   # uv lock file
├── package-lock.json         # frontend lock file if generated at root
├── .gitignore
└── README.md