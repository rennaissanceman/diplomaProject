from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from starlette.middleware.cors import CORSMiddleware
from mimetypes import guess_type
from datetime import datetime

from db import Base, engine, get_db
from router import route_with_langgraph
from runtime import run_agent_with_debug
from ollama_client import list_llm_models
from models import Agent, AgentLink
from schemas import (
    AgentCreate,
    AgentResponse,
    AgentUpdateSafe,
    ChatRequest,
    ChatResponse,
    ChatDebugResponse,
    RetrievedChunkResponse,
)

import logging
import re
import shutil
import os


logging.basicConfig(
    level=logging.ERROR,
    format="%(levelname)s | %(name)s | %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Diploma project",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("data").resolve()


def to_agent_response(agent: Agent) -> AgentResponse:
    connected_agent_ids = [
        link.child_agent_id
        for link in getattr(agent, "supervisor_links", [])
        if link.active
    ]

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        docs_path=agent.docs_path,
        prompt=agent.prompt,
        agent_type=agent.agent_type,
        active=agent.active,
        connected_agent_ids=connected_agent_ids,
    )


def validate_connected_agents(
    db: Session,
    connected_agent_ids: list[int],
    supervisor_id: int,
) -> None:
    if not connected_agent_ids:
        return

    child_agents = db.query(Agent).filter(Agent.id.in_(connected_agent_ids)).all()

    if len(child_agents) != len(set(connected_agent_ids)):
        raise HTTPException(
            status_code=400,
            detail="One or more connected agents do not exist",
        )

    for child in child_agents:
        if child.id == supervisor_id:
            raise HTTPException(
                status_code=400,
                detail="Supervisor cannot be linked to itself",
            )


def create_supervisor_links(
    db: Session,
    supervisor_id: int,
    connected_agent_ids: list[int],
) -> None:
    if not connected_agent_ids:
        return

    validate_connected_agents(
        db=db,
        connected_agent_ids=connected_agent_ids,
        supervisor_id=supervisor_id,
    )

    links = [
        AgentLink(
            supervisor_agent_id=supervisor_id,
            child_agent_id=child_id,
            active=True,
            sort_order=index + 1,
        )
        for index, child_id in enumerate(connected_agent_ids)
    ]

    db.add_all(links)
    db.commit()


@app.get("/llm-models")
def get_llm_models():
    return list_llm_models()


@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}


@app.get("/agents", response_model=list[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).order_by(Agent.id.asc()).all()
    return [to_agent_response(agent) for agent in agents]


@app.post("/agents", response_model=AgentResponse)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)):
    existing_agent = db.query(Agent).filter(Agent.name == payload.name).first()

    if existing_agent:
        raise HTTPException(
            status_code=400,
            detail="Agent already exists",
        )

    if payload.agent_type == "specialist" and payload.connected_agent_ids:
        raise HTTPException(
            status_code=400,
            detail="Only supervisor agents can have connected agents",
        )

    if payload.agent_type == "supervisor" and not payload.connected_agent_ids:
        raise HTTPException(
            status_code=400,
            detail="Supervisor agent must have at least one connected agent",
        )

    agent = Agent(
        name=payload.name,
        description=payload.description,
        docs_path=payload.docs_path,
        prompt=payload.prompt,
        agent_type=payload.agent_type,
        active=payload.active,
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    Path(agent.docs_path).mkdir(parents=True, exist_ok=True)

    if payload.agent_type == "supervisor":
        create_supervisor_links(
            db=db,
            supervisor_id=agent.id,
            connected_agent_ids=payload.connected_agent_ids,
        )

    agent = db.query(Agent).filter(Agent.id == agent.id).first()
    return to_agent_response(agent)


@app.patch("/agents/{agent_id}/deactivate")
def deactivate_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    agent.active = False

    db.query(AgentLink).filter(
        or_(
            AgentLink.supervisor_agent_id == agent.id,
            AgentLink.child_agent_id == agent.id,
        )
    ).update({"active": False}, synchronize_session=False)

    db.commit()

    return {
        "message": f"Agent '{agent.name}' was deactivated successfully",
    }


@app.patch("/agents/{agent_id}/activate")
def activate_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    agent.active = True

    db.query(AgentLink).filter(
        or_(
            AgentLink.supervisor_agent_id == agent.id,
            AgentLink.child_agent_id == agent.id,
        )
    ).update({"active": True}, synchronize_session=False)

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return {
        "message": f"Agent '{agent.name}' was activated successfully",
    }


@app.patch("/agents/{agent_id}")
def update_agent(agent_id: int, data: AgentUpdateSafe, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    agent.name = data.name
    agent.description = data.description
    agent.prompt = data.prompt

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return {
        "message": f"Agent '{agent.name}' updated successfully",
        "agent": {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "prompt": agent.prompt,
        },
    }


rag_metrics_store = []


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    agent_name = route_with_langgraph(
        db=db,
        question=payload.question,
        selected_agent=payload.selected_agent,
    )

    agent = (
        db.query(Agent)
        .filter(Agent.name == agent_name, Agent.active.is_(True))
        .first()
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    answer, sources, debug = run_agent_with_debug(
        question=payload.question,
        agent=agent,
        db=db,
        language_model=payload.language_model,
        use_reranker=payload.use_reranker,
    )

    rag_metrics_store.append(
        {
            "retrieval_time_ms": debug.retrieval_time_ms,
            "reranking_time_ms": debug.reranking_time_ms,
            "generation_time_ms": debug.generation_time_ms,
            "total_time_ms": debug.total_time_ms,
            "confidence": debug.confidence,
            "agent_type": debug.agent_type,
            "language_model": debug.language_model,
            "use_reranker": debug.use_reranker,
            "chunks": len(debug.chunks),
        }
    )

    return ChatResponse(
        agent=agent.name,
        answer=answer,
        sources=sources,
        debug=ChatDebugResponse(
            agent_type=debug.agent_type,
            language_model=debug.language_model,
            use_reranker=debug.use_reranker,
            retrieval_time_ms=debug.retrieval_time_ms,
            reranking_time_ms=debug.reranking_time_ms,
            generation_time_ms=debug.generation_time_ms,
            total_time_ms=debug.total_time_ms,
            confidence=debug.confidence,
            chunks=[
                RetrievedChunkResponse(
                    agent=item.chunk.agent_name,
                    source_file=item.chunk.source_file,
                    chunk_id=item.chunk.chunk_id,
                    score=round(item.score, 4),
                    start_char=item.chunk.start_char,
                    end_char=item.chunk.end_char,
                    content=item.chunk.content,
                )
                for item in debug.chunks
            ],
        ),
    )


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


@app.post("/documents/upload")
async def upload_documents(
    folder_name: str = Form(...),
    files: list[UploadFile] = File(...),
):
    if not re.match(r"^[a-zA-Z0-9_-]+$", folder_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid folder name",
        )

    target_folder = (DATA_DIR / folder_name).resolve()

    if DATA_DIR not in target_folder.parents and target_folder != DATA_DIR:
        raise HTTPException(
            status_code=400,
            detail="Invalid folder path",
        )

    target_folder.mkdir(parents=True, exist_ok=True)

    saved_files: list[str] = []

    for file in files:
        if not file.filename:
            continue

        ext = Path(file.filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}",
            )

        file_path = target_folder / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved_files.append(file.filename)

    return {
        "message": "Files uploaded successfully",
        "folder": folder_name,
        "files": saved_files,
    }


@app.get("/documents/{folder_name}")
async def get_documents(folder_name: str):
    if not re.match(r"^[a-zA-Z0-9_-]+$", folder_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid folder name",
        )

    target_folder = (DATA_DIR / folder_name).resolve()

    if DATA_DIR not in target_folder.parents and target_folder != DATA_DIR:
        raise HTTPException(
            status_code=400,
            detail="Invalid folder path",
        )

    if not target_folder.exists():
        raise HTTPException(
            status_code=404,
            detail="Folder not found",
        )

    documents = []

    for file_path in target_folder.iterdir():
        if not file_path.is_file():
            continue

        documents.append(
            {
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "size_bytes": file_path.stat().st_size,
                "modified_at": datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                ).isoformat(),
            }
        )

    documents.sort(
        key=lambda item: item["modified_at"],
        reverse=True,
    )

    return {
        "folder": folder_name,
        "documents": documents,
    }


@app.get("/documents/{folder_name}/{filename}")
async def get_document(
    folder_name: str,
    filename: str,
    download: bool = False,
):
    if not re.match(r"^[a-zA-Z0-9_-]+$", folder_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid folder name",
        )

    target_folder = (DATA_DIR / folder_name).resolve()
    file_path = (target_folder / filename).resolve()

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    if target_folder not in file_path.parents:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    mime_type, _ = guess_type(file_path)

    if download:
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment"},
        )

    return FileResponse(
        path=file_path,
        media_type=mime_type or "text/plain",
        headers={"Content-Disposition": "inline"},
    )


@app.delete("/documents/{folder_name}/{filename}")
async def delete_document(
    folder_name: str,
    filename: str,
):
    if not re.match(r"^[a-zA-Z0-9_-]+$", folder_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid folder name",
        )

    target_folder = (DATA_DIR / folder_name).resolve()

    if DATA_DIR not in target_folder.parents and target_folder != DATA_DIR:
        raise HTTPException(
            status_code=400,
            detail="Invalid folder path",
        )

    file_path = (target_folder / filename).resolve()

    if target_folder not in file_path.parents:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    file_path.unlink()

    return {
        "message": "File deleted successfully",
        "folder": folder_name,
        "filename": filename,
    }


@app.get("/documents")
async def list_document_folders():
    if not DATA_DIR.exists():
        return {"folders": []}

    folders = []

    for path in DATA_DIR.iterdir():
        if path.is_dir():
            folders.append(
                {
                    "name": path.name,
                }
            )

    return {
        "folders": folders,
    }


@app.get("/metrics/rag")
def get_rag_metrics():
    if not rag_metrics_store:
        return {
            "avg_retrieval_time_ms": 0,
            "avg_reranking_time_ms": 0,
            "avg_generation_time_ms": 0,
            "avg_total_time_ms": 0,
            "avg_confidence": 0,
            "requests": 0,
            "reranker_requests": 0,
        }

    n = len(rag_metrics_store)

    return {
        "avg_retrieval_time_ms": sum(
            item["retrieval_time_ms"] for item in rag_metrics_store
        ) / n,
        "avg_reranking_time_ms": sum(
            item["reranking_time_ms"] for item in rag_metrics_store
        ) / n,
        "avg_generation_time_ms": sum(
            item["generation_time_ms"] for item in rag_metrics_store
        ) / n,
        "avg_total_time_ms": sum(
            item["total_time_ms"] for item in rag_metrics_store
        ) / n,
        "avg_confidence": sum(
            item["confidence"] for item in rag_metrics_store
        ) / n,
        "requests": n,
        "reranker_requests": sum(
            1 for item in rag_metrics_store if item["use_reranker"]
        ),
    }