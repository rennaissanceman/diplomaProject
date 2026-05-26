import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from sentence_transformers import CrossEncoder

from retrieval.types import RetrievedChunk


API_DIR = Path(__file__).resolve().parents[1]

DEFAULT_RERANKER_MODEL = (
    API_DIR
    / "local_models"
    / "reranker"
    / "qwen3-reranker-0.6b-seq-cls"
)

DEFAULT_RERANKER_CANDIDATES = 20
DEFAULT_RERANKER_TOP_K = 3


def _force_offline_mode() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"


def _sigmoid(value: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-value))
    except OverflowError:
        return 0.0 if value < 0 else 1.0


def _to_float_scores(raw_scores: Iterable) -> list[float]:
    """
    CrossEncoder.predict() can return:
    - list[float],
    - numpy.ndarray,
    - list[list[float]],
    - numpy.ndarray with shape (n, 1).

    This helper normalizes output to list[float].
    """
    normalized_scores: list[float] = []

    for raw_score in raw_scores:
        if isinstance(raw_score, (list, tuple)):
            normalized_scores.append(float(raw_score[0]))
        elif hasattr(raw_score, "tolist"):
            converted = raw_score.tolist()

            if isinstance(converted, list):
                normalized_scores.append(float(converted[0]))
            else:
                normalized_scores.append(float(converted))
        else:
            normalized_scores.append(float(raw_score))

    return normalized_scores


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    _force_offline_mode()

    if not DEFAULT_RERANKER_MODEL.exists():
        raise FileNotFoundError(
            "Local reranker model not found. Run: uv run python download_models.py"
        )

    return CrossEncoder(
        str(DEFAULT_RERANKER_MODEL),
        trust_remote_code=True,
        local_files_only=True,
    )


def rerank_chunks(
    question: str,
    chunks: list[RetrievedChunk],
    top_k: int = DEFAULT_RERANKER_TOP_K,
) -> list[RetrievedChunk]:
    if not question.strip():
        return []

    if not chunks:
        return []

    if top_k <= 0:
        return []

    reranker = get_reranker()

    pairs = [
        [question, item.chunk.content]
        for item in chunks
    ]

    raw_scores = reranker.predict(pairs)
    float_scores = _to_float_scores(raw_scores)

    scored_items: list[tuple[float, RetrievedChunk]] = []

    for item, raw_score in zip(chunks, float_scores):
        normalized_score = round(_sigmoid(raw_score), 4)

        scored_items.append(
            (
                normalized_score,
                RetrievedChunk(
                    chunk=item.chunk,
                    score=normalized_score,
                ),
            )
        )

    scored_items.sort(
        key=lambda pair: pair[0],
        reverse=True,
    )

    return [
        item
        for _, item in scored_items[:top_k]
    ]