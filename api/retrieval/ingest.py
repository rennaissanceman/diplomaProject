import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from retrieval.retriever import build_index_for_folder
from retrieval.vector_store import DEFAULT_INDEXES_ROOT

API_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_DIR.parent

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

@dataclass(frozen=True)
class AgentConfig:
    id: int
    name: str
    docs_path: str
    agent_type: str
    active: bool


def resolve_docs_path(raw_docs_path: str) -> Path:
    path = Path(raw_docs_path)

    if path.is_absolute():
        return path

    candidates = [
        PROJECT_ROOT / raw_docs_path,
        API_DIR / raw_docs_path,
        Path.cwd() / raw_docs_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return (API_DIR / raw_docs_path).resolve()


def load_agents_from_db(db_path: Path) -> list[AgentConfig]:
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT id, name, docs_path, agent_type, active
            FROM agents
            WHERE active = 1
            ORDER BY id ASC
            """
        ).fetchall()
    finally:
        connection.close()

    agents: list[AgentConfig] = []

    for row in rows:
        agents.append(
            AgentConfig(
                id=int(row["id"]),
                name=str(row["name"]),
                docs_path=str(row["docs_path"]),
                agent_type=str(row["agent_type"]),
                active=bool(row["active"]),
            )
        )

    return agents


def find_agent(
    agents: list[AgentConfig],
    agent_name: str,
) -> AgentConfig:
    normalized = agent_name.strip().lower()

    for agent in agents:
        if agent.name.strip().lower() == normalized:
            return agent

    available = ", ".join(agent.name for agent in agents)
    raise ValueError(
        f"Agent '{agent_name}' not found. Available active agents: {available}"
    )


def ingest_agent(
    agent: AgentConfig,
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    resolved_docs_path = resolve_docs_path(agent.docs_path)

    if not resolved_docs_path.exists():
        raise FileNotFoundError(
            f"Docs path for agent '{agent.name}' does not exist: {resolved_docs_path}"
        )

    if not resolved_docs_path.is_dir():
        raise NotADirectoryError(
            f"Docs path for agent '{agent.name}' is not a directory: {resolved_docs_path}"
        )

    chunk_count = build_index_for_folder(
        folder=str(resolved_docs_path),
        agent_name=agent.name,
        indexes_root=DEFAULT_INDEXES_ROOT,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    print(
        f"[OK] agent={agent.name} "
        f"type={agent.agent_type} "
        f"docs={resolved_docs_path} "
        f"chunks={chunk_count}"
    )

    return chunk_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline ingest pipeline for per-agent RAG indexes."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--agent",
        help="Name of one agent to ingest, for example: hr, lotr, hogwart",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Build indexes for all active agents",
    )

    parser.add_argument(
        "--db",
        default=str(API_DIR / "agents.db"),
        help="Path to SQLite agents database",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1200,
        help="Chunk size in characters",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Chunk overlap in characters",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    agents = load_agents_from_db(Path(args.db))

    if args.agent:
        selected_agents = [find_agent(agents, args.agent)]
    else:
        selected_agents = [
            agent for agent in agents
            if agent.agent_type == "specialist"
        ]

    selected_agents = [
        agent for agent in selected_agents
        if agent.agent_type == "specialist"
    ]

    total_chunks = 0

    for agent in selected_agents:
        total_chunks += ingest_agent(
            agent=agent,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )

    print(f"[DONE] indexed_agents={len(selected_agents)} total_chunks={total_chunks}")
    print(f"[INDEXES] {DEFAULT_INDEXES_ROOT}")


if __name__ == "__main__":
    main()