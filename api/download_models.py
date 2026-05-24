import os
from pathlib import Path

from huggingface_hub import snapshot_download


BASE_DIR = Path(__file__).resolve().parent

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MODEL_REPO_ID = "sentence-transformers/all-MiniLM-L6-v2"

RERANKER_MODEL_NAME = "qwen3-reranker-0.6b-seq-cls"
RERANKER_MODEL_REPO_ID = "tomaarsen/Qwen3-Reranker-0.6B-seq-cls"

EMBEDDING_MODEL_DIR = (
    BASE_DIR
    / "local_models"
    / "embedding"
    / EMBEDDING_MODEL_NAME
)

RERANKER_MODEL_DIR = (
    BASE_DIR
    / "local_models"
    / "reranker"
    / RERANKER_MODEL_NAME
)


def allow_online_download() -> None:
    os.environ.pop("HF_HUB_OFFLINE", None)
    os.environ.pop("TRANSFORMERS_OFFLINE", None)
    os.environ.pop("HF_DATASETS_OFFLINE", None)


def model_exists(model_dir: Path) -> bool:
    return model_dir.exists() and any(model_dir.iterdir())


def download_snapshot(repo_id: str, model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)

    print(f"[DOWNLOAD] {repo_id}")
    print(f"[TARGET]   {model_dir}")

    snapshot_download(
        repo_id=repo_id,
        local_dir=model_dir,
    )

    print(f"[OK] Downloaded model to: {model_dir}")


def main() -> None:
    allow_online_download()

    if model_exists(EMBEDDING_MODEL_DIR):
        print(f"[OK] Local embedding model already exists: {EMBEDDING_MODEL_DIR}")
    else:
        print(f"[MISSING] Local embedding model missing: {EMBEDDING_MODEL_DIR}")
        download_snapshot(
            repo_id=EMBEDDING_MODEL_REPO_ID,
            model_dir=EMBEDDING_MODEL_DIR,
        )

    if model_exists(RERANKER_MODEL_DIR):
        print(f"[OK] Local reranker model already exists: {RERANKER_MODEL_DIR}")
    else:
        print(f"[MISSING] Local reranker model missing: {RERANKER_MODEL_DIR}")
        download_snapshot(
            repo_id=RERANKER_MODEL_REPO_ID,
            model_dir=RERANKER_MODEL_DIR,
        )


if __name__ == "__main__":
    main()