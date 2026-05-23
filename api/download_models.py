import os
from pathlib import Path

from huggingface_hub import snapshot_download


BASE_DIR = Path(__file__).resolve().parent

MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_REPO_ID = "sentence-transformers/all-MiniLM-L6-v2"

MODEL_DIR = (
    BASE_DIR
    / "local_models"
    / "embedding"
    / MODEL_NAME
)

REQUIRED_FILES = [
    "config.json",
    "modules.json",
    "sentence_bert_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "model.safetensors",
]


def model_exists() -> bool:
    return MODEL_DIR.exists() and all(
        (MODEL_DIR / file_name).exists()
        for file_name in REQUIRED_FILES
    )


def allow_online_download() -> None:
    os.environ.pop("HF_HUB_OFFLINE", None)
    os.environ.pop("TRANSFORMERS_OFFLINE", None)
    os.environ.pop("HF_DATASETS_OFFLINE", None)


def download_model() -> None:
    allow_online_download()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[DOWNLOAD] {MODEL_REPO_ID}")
    print(f"[TARGET]   {MODEL_DIR}")

    snapshot_download(
        repo_id=MODEL_REPO_ID,
        local_dir=MODEL_DIR,
    )

    print(f"[OK] Downloaded model to: {MODEL_DIR}")


def main() -> None:
    if model_exists():
        print(f"[OK] Local model already exists: {MODEL_DIR}")
        return

    print(f"[MISSING] Local model incomplete or missing: {MODEL_DIR}")
    download_model()


if __name__ == "__main__":
    main()