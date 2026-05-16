# Project Name
diplomaProject

# Description
This project implements a **Multi-Agent Retrieval-Augmented Generation (Multi-RAG)** system using a local LLM stack.
Each agent has:

- its own documents (`api/data/<agent>/`)
- its own FAISS vector index (`api/indexes/<agent>/`)
- its own retrieval pipeline

The system performs:

1. Retrieval (top-k chunks)
2. Prompt construction
3. Answer generation via local LLM (Ollama)

## Key Features

- Multi-agent architecture (specialists + supervisor)
- Per-agent RAG (separate indexes)
- Semantic retrieval (embeddings)
- FAISS vector search
- Offline ingest pipeline
- Debug metadata
- React UI
- Fully local execution

# Technologies Used
- Python 3.12
- FastAPI
- HTML / CSS
- uv python env
- Ollama 

# Requirements
- python: 3.12
- uv: 0.9.28
- node.js: v24.13.0
- Ollama client 
- llama3.2:1b model

# Assumptions

- Small LLM (llama3.2:1b)
- No reranking yet
- No semantic routing
- Confidence is heuristic

# Future development

- semantic routing
- hybrid retrieval (BM25 + embeddings)
- reranking layer
- evaluation pipeline
- multi-agent comparison

# Project Structure
```
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
│       │   │   ├── agentsConfiguration.js
│       │   │   ├── agentsOverview.js
│       │   │   ├── documentsManagement.js
│       │   │   └── liveStatus.js
│       │   │ 
│       │   ├── AiAssistant.js     # main chat UI with RAG debug
│       │   ├── Dashboard.js       # management panel
│       │   ├── Home.js            # Homepage
│       │   └── Scenarios.js       # Solution Tests
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
```
## Files ignored by Git
The project uses `.gitignore` to exclude virtual environments, environment
variables, cache files, etc.

## Installation
1. Clone the repository:
```
https://github.com/agorkaissi/diplomaProject.git
```
2. Create and Activate a virtual environment & install all dependencies:
- Backend (Python / FastAPI)
```
cd diplomaProject
uv sync
```
- Frontend (UI / Node)
```
cd diplomaProject/ui
npm install
```
3. Prepare Ollama client 
- download and install ollama client from: https://ollama.com/download
```
ollama list
ollama pull llama3.2:1b
ollama run llama3.2:1b
```

4.Builds FAISS indexes (Required before first use)
 - for all agents. 
```
cd diplomaProject/api
uv run python -m retrieval.ingest --all
```
- for a single agent.
```
cd diplomaProject/api
uv run python -m retrieval.ingest --agent hr
```

## Running the Application
- Backend (separate console)
```
cd diplomaProject/api
uv run uvicorn main:app --reload
```
- Frontend (separate console)
```
cd diplomaProject/ui
npm start
```
then open your browser (Tested on Brave) and open:

The application will be available at:
http://localhost:3000

Interactive Swagger documentation:
http://127.0.0.1:8000/docs

Redoc documentation:
http://127.0.0.1:8000/redoc
