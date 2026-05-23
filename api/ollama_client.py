from functools import lru_cache

from langchain_ollama import ChatOllama


OLLAMA_BASE_URL = "http://127.0.0.1:11434"

DEFAULT_OLLAMA_MODEL = "llama3.2:1b"

ALLOWED_OLLAMA_MODELS = {
    "llama3.2:1b": {
        "label": "Llama 3.2 1B",
        "description": "A lightweight local model that runs quickly on less powerful hardware.",
    },
    "gemma2:2b": {
        "label": "Gemma 2 2B",
        "description": "The local Google Gemma model is higher quality but heavier.",
    },
}


def list_llm_models() -> list[dict]:
    return [
        {
            "id": model_id,
            "label": metadata["label"],
            "description": metadata["description"],
            "default": model_id == DEFAULT_OLLAMA_MODEL,
        }
        for model_id, metadata in ALLOWED_OLLAMA_MODELS.items()
    ]


def validate_model_name(model_name: str | None) -> str:
    if not model_name:
        return DEFAULT_OLLAMA_MODEL

    if model_name not in ALLOWED_OLLAMA_MODELS:
        allowed = ", ".join(ALLOWED_OLLAMA_MODELS.keys())
        raise ValueError(f"Unsupported LLM model: {model_name}. Allowed: {allowed}")

    return model_name


@lru_cache(maxsize=8)
def get_llm(model_name: str) -> ChatOllama:
    return ChatOllama(
        model=model_name,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
        timeout=60,
    )


def generate_answer(prompt: str, model_name: str | None = None) -> str:
    selected_model = validate_model_name(model_name)
    llm = get_llm(selected_model)
    response = llm.invoke(prompt)
    return response.content