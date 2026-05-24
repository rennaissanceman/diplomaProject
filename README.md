# Project Name

diplomaProject

---

# Description

This project implements a **Multi-Agent Retrieval-Augmented Generation (Multi-RAG)** system using a fully local LLM stack.

Each agent has:

- its own documents (`api/data/<agent>/`)
- its own FAISS vector index (`api/indexes/<agent>/`)
- its own retrieval pipeline

The system supports:

1. Semantic retrieval (FAISS)
2. Optional reranking layer (Qwen Reranker)
3. Prompt construction
4. Answer generation via local LLMs (Ollama)

The entire pipeline works locally and supports offline execution after model download.

---

# Key Features

- Multi-agent architecture (specialists + supervisor)
- Per-agent RAG (separate indexes)
- Semantic retrieval (embeddings)
- FAISS vector search
- Offline ingest pipeline
- Offline HuggingFace embeddings
- Local reranking layer (Qwen Reranker)
- Multi-LLM support
- Dynamic LLM selection from frontend
- Dynamic reranker toggle from frontend
- Ollama integration
- React UI
- RAG debug metrics
- Retrieved chunk preview
- Fully local execution
- Offline-ready architecture

---

# Technologies Used

- Python 3.12
- FastAPI
- React
- Ollama
- FAISS
- HuggingFace Transformers
- SentenceTransformers
- SQLAlchemy
- SQLite
- LangGraph

---

# Requirements

- Python 3.12
- uv 0.9.28+
- Node.js v24+
- Ollama client
- llama3.2:1b model
- gemma2:2b model

---

# Assumptions

- Local execution only
- FAISS-based semantic retrieval
- Ollama used for local inference
- Qwen reranker is optional
- Confidence is heuristic
- Small local LLMs optimized for consumer hardware

---

# Future development

- semantic routing
- hybrid retrieval (BM25 + embeddings)
- multilingual embeddings
- benchmarking pipeline
- automated evaluation
- vector databases (Qdrant / ChromaDB)
- advanced reranking strategies
- response streaming
- GPU acceleration

---

# Supported Local Models

## Language Models (Ollama)

- llama3.2:1b
- gemma2:2b

## Embedding Models

- all-MiniLM-L6-v2

## Reranker Models

- Qwen3-Reranker-0.6B-seq-cls

---

# RAG Pipeline

The runtime pipeline:

```text
question
→ FAISS retrieval
→ optional Qwen reranking
→ prompt construction
→ local LLM generation
→ response
```

The reranker can be enabled or disabled dynamically from the frontend UI.

---

# Project Structure

```text
diplomaProject/
├── api/
│   ├── data/
│   │   ├── hogwart/
│   │   ├── hr/
│   │   ├── lotr/
│   │   └── PanTadeusz/
│   │
│   ├── indexes/
│   │   ├── hr/
│   │   ├── harrypotter/
│   │   ├── frodo/
│   │   └── ksrobak/
│   │
│   ├── local_models/
│   │   ├── embedding/
│   │   └── reranker/
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── builders.py
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── ingest.py
│   │   ├── reranker.py
│   │   ├── retriever.py
│   │   ├── types.py
│   │   └── vector_store.py
│   │
│   ├── agents.db
│   ├── db.py
│   ├── download_models.py
│   ├── main.py
│   ├── models.py
│   ├── ollama_client.py
│   ├── router.py
│   ├── runtime.py
│   ├── schemas.py
│   └── test_main.http
│
├── ui/
│   ├── public/
│   └── src/
│       ├── pages/
│       │   ├── dashboard/
│       │   ├── AiAssistant.js
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
├── pyproject.toml
├── uv.lock
├── package-lock.json
├── .gitignore
└── README.md
```

---

# Files ignored by Git

The project uses `.gitignore` to exclude:

- virtual environments
- environment variables
- cache files
- local runtime artifacts
- temporary files
- generated indexes
- local model cache

---

# Installation

## 1. Clone repository

```bash
git clone https://github.com/agorkaissi/diplomaProject.git
```

---

## 2. Install backend dependencies

```bash
cd diplomaProject
uv sync
```

---

## 3. Install frontend dependencies

```bash
cd diplomaProject/ui
npm install
```

---

# Prepare Ollama client

Download and install Ollama:

https://ollama.com/download

Check installed models:

```bash
ollama list
```

Download required local models:

```bash
ollama pull llama3.2:1b
ollama pull gemma2:2b
```

Optional manual test:

```bash
ollama run llama3.2:1b
ollama run gemma2:2b
```

---

# Download local embedding and reranker models

```bash
cd diplomaProject/api
uv run python download_models.py
```

This downloads:

- embedding model
- Qwen reranker model

to local directories:

- `api/local_models/embedding/`
- `api/local_models/reranker/`

---

# Build FAISS indexes (required before first use)

## Build indexes for all agents

```bash
cd diplomaProject/api
uv run python -m retrieval.ingest --all
```

---

## Build index for a single agent

```bash
cd diplomaProject/api
uv run python -m retrieval.ingest --agent hr
```

---

# Running the Application

## Backend (separate console)

```bash
cd diplomaProject/api
uv run uvicorn main:app --reload
```

---

## Frontend (separate console)

```bash
cd diplomaProject/ui
npm start
```

Then open browser:

```text
http://localhost:3000
```

---

# API Documentation

## Swagger

```text
http://127.0.0.1:8000/docs
```

---

## ReDoc

```text
http://127.0.0.1:8000/redoc
```

---

# API Endpoints

## Core endpoints

- GET `/healthcheck`
- GET `/agents`
- POST `/chat`

---

## LLM endpoints

- GET `/llm-models`

---

## Metrics

- GET `/metrics/rag`

---

## Documents

- POST `/documents/upload`
- GET `/documents`
- GET `/documents/{folder}`
- DELETE `/documents/{folder}/{filename}`

---

# Debug Metrics

The system exposes runtime RAG metrics:

- retrieval time
- reranking time
- generation time
- total response time
- retrieval confidence
- retrieved chunks
- source files

Metrics are visible directly in the frontend UI and available through API responses.

---

# Benchmark Notes

Preliminary benchmarks indicate:

- Gemma 2B provides higher answer quality
- Llama 1B is significantly faster
- Qwen reranker improves chunk selection quality
- Reranking introduces noticeable latency on CPU-only hardware
- Fully local RAG execution is possible on consumer-grade hardware