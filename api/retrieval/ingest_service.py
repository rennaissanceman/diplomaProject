from pathlib import Path
from sqlalchemy.orm import Session

from models import Agent
from retrieval.ingest import resolve_docs_path
from retrieval.retriever import build_index_for_folder
from retrieval.vector_store import DEFAULT_INDEXES_ROOT


DEFAULT_CHUNK_SIZE = 700
DEFAULT_CHUNK_OVERLAP = 120


def ingest_agent(
    agent: Agent,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict:
    resolved_docs_path = resolve_docs_path(agent.docs_path)

    if not resolved_docs_path.exists():
        return {
            "status": "error",
            "agent": agent.name,
            "message": f"Docs path does not exist: {resolved_docs_path}",
        }

    if not resolved_docs_path.is_dir():
        return {
            "status": "error",
            "agent": agent.name,
            "message": f"Docs path is not a directory: {resolved_docs_path}",
        }

    chunk_count = build_index_for_folder(
        folder=str(resolved_docs_path),
        agent_name=agent.name,
        indexes_root=DEFAULT_INDEXES_ROOT,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return {
        "status": "ok",
        "agent": agent.name,
        "agent_type": agent.agent_type,
        "docs_path": str(resolved_docs_path),
        "chunks": chunk_count,
        "index_root": str(DEFAULT_INDEXES_ROOT),
    }


def ingest_agent_by_name(
    db: Session,
    agent_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict:
    agent = (
        db.query(Agent)
        .filter(Agent.name == agent_name)
        .filter(Agent.active.is_(True))
        .first()
    )

    if not agent:
        return {
            "status": "error",
            "message": f"Active agent not found: {agent_name}",
        }

    if agent.agent_type != "specialist":
        return {
            "status": "error",
            "agent": agent.name,
            "message": "Only specialist agents can be ingested.",
        }

    return ingest_agent(
        agent=agent,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def ingest_all_agents(
    db: Session,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict:
    agents = (
        db.query(Agent)
        .filter(Agent.active.is_(True))
        .filter(Agent.agent_type == "specialist")
        .order_by(Agent.id.asc())
        .all()
    )

    results = []

    for agent in agents:
        results.append(
            ingest_agent(
                agent=agent,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )

    total_chunks = sum(
        item.get("chunks", 0)
        for item in results
        if item.get("status") == "ok"
    )

    return {
        "status": "ok",
        "mode": "all",
        "agents_count": len(agents),
        "total_chunks": total_chunks,
        "results": results,
    }