import os
from functools import lru_cache
from pathlib import Path

import numpy as np

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from sentence_transformers import SentenceTransformer


API_DIR = Path(__file__).resolve().parents[1]

DEFAULT_EMBEDDING_MODEL = str(
    API_DIR
    / "local_models"
    / "embedding"
    / "all-MiniLM-L6-v2"
)


@lru_cache(maxsize=1)
def get_embedding_model(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> SentenceTransformer:
    model_path = Path(model_name).resolve()

    if not model_path.exists():
        raise FileNotFoundError(
            f"Local embedding model not found: {model_path}. "
            f"Run: uv run python download_models.py"
        )

    return SentenceTransformer(
        str(model_path),
        local_files_only=True,
    )


def embed_texts(
    texts: list[str],
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    model = get_embedding_model(model_name)

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embeddings.astype(np.float32)


def embed_text(
    text: str,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> np.ndarray:
    embeddings = embed_texts([text], model_name=model_name)

    if embeddings.shape[0] == 0:
        return np.empty((0,), dtype=np.float32)

    return embeddings[0]


def cosine_similarity(
    query_embedding: np.ndarray,
    document_embeddings: np.ndarray,
) -> np.ndarray:
    if query_embedding.size == 0 or document_embeddings.size == 0:
        return np.array([], dtype=np.float32)

    scores = np.matmul(document_embeddings, query_embedding)

    return scores.astype(np.float32)