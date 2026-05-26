from retrieval.types import DocumentChunk, SourceDocument

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 200


def chunk_document(
    document: SourceDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = document.content
    if not text.strip():
        return []

    chunks: list[DocumentChunk] = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        raw_chunk = text[start:end]
        chunk_content = raw_chunk.strip()

        if chunk_content:
            chunk_id = f"{document.document_id}::chunk_{chunk_index}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    source_file=document.source_file,
                    docs_path=document.docs_path,
                    content=chunk_content,
                    start_char=start,
                    end_char=end,
                    agent_name=document.agent_name,
                )
            )
            chunk_index += 1

        if end >= len(text):
            break

        next_start = end - chunk_overlap
        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def chunk_documents(
    documents: list[SourceDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []

    for document in documents:
        chunks.extend(
            chunk_document(
                document=document,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )

    return chunks