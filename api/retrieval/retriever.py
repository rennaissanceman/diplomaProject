from pathlib import Path

from retrieval.chunking import chunk_documents
from retrieval.loader import load_documents
from retrieval.types import RetrievedChunk, SourceDocument
from retrieval.vector_store import (
    DEFAULT_INDEXES_ROOT,
    get_agent_index_dir,
    index_exists,
    save_vector_index,
    search_vector_index,
)
from retrieval.reranker import DEFAULT_RERANKER_CANDIDATES, rerank_chunks

DEFAULT_TOP_K = 3
MIN_SIMILARITY_SCORE = 0.25


def _build_source_documents(
    folder: str,
    agent_name: str | None = None,
) -> list[SourceDocument]:
    loaded_documents = load_documents(folder)

    source_documents: list[SourceDocument] = []

    for file_name, content in loaded_documents:
        source_documents.append(
            SourceDocument(
                document_id=f"{folder}:{file_name}",
                source_file=file_name,
                content=content,
                docs_path=folder,
                agent_name=agent_name,
            )
        )

    return source_documents


def build_index_for_folder(
    folder: str,
    agent_name: str | None = None,
    indexes_root: Path = DEFAULT_INDEXES_ROOT,
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> int:
    index_dir = get_agent_index_dir(
        docs_path=folder,
        agent_name=agent_name,
        indexes_root=indexes_root,
    )

    source_documents = _build_source_documents(
        folder=folder,
        agent_name=agent_name,
    )

    if not source_documents:
        return 0

    chunks = chunk_documents(
        documents=source_documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not chunks:
        return 0

    save_vector_index(
        chunks=chunks,
        index_dir=index_dir,
    )

    return len(chunks)


def retrieve_chunks_for_folder(
    question: str,
    folder: str,
    top_k: int = DEFAULT_TOP_K,
    agent_name: str | None = None,
    min_score: float = MIN_SIMILARITY_SCORE,
    use_reranker: bool = False,
    reranker_candidates: int = DEFAULT_RERANKER_CANDIDATES,
) -> list[RetrievedChunk]:
    index_dir = get_agent_index_dir(
        docs_path=folder,
        agent_name=agent_name,
        indexes_root=DEFAULT_INDEXES_ROOT,
    )

    if not index_exists(index_dir):
        return []

    vector_top_k = reranker_candidates if use_reranker else top_k

    vector_results = search_vector_index(
        question=question,
        index_dir=index_dir,
        top_k=vector_top_k,
        min_score=0.0 if use_reranker else min_score,
    )

    if not vector_results:
        return []

    if not use_reranker:
        return vector_results[:top_k]

    return rerank_chunks(
        question=question,
        chunks=vector_results,
        top_k=top_k,
    )