import os

from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PROVIDER = os.getenv("OPENAI_PROVIDER", os.getenv("LOCAL_LLM_PROVIDER", "openai")).strip()
DEFAULT_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8002/v1").rstrip("/")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY", "dummy")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL_NAME", "llama-3.3-70b-instruct")
DEFAULT_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))


def _get_role_setting(role: str, suffix: str, default: str) -> str:
    return os.getenv(f"OPENAI_{role}_{suffix}", default)


WORKER_PROVIDER = _get_role_setting("WORKER", "PROVIDER", DEFAULT_PROVIDER).strip()
WORKER_BASE_URL = _get_role_setting("WORKER", "API_BASE", DEFAULT_BASE_URL).rstrip("/")
WORKER_API_KEY = _get_role_setting("WORKER", "API_KEY", DEFAULT_API_KEY)
WORKER_MODEL = _get_role_setting("WORKER", "MODEL_NAME", DEFAULT_MODEL)

MANAGER_PROVIDER = _get_role_setting("MANAGER", "PROVIDER", DEFAULT_PROVIDER).strip()
MANAGER_BASE_URL = _get_role_setting("MANAGER", "API_BASE", DEFAULT_BASE_URL).rstrip("/")
MANAGER_API_KEY = _get_role_setting("MANAGER", "API_KEY", DEFAULT_API_KEY)
MANAGER_MODEL = _get_role_setting("MANAGER", "MODEL_NAME", DEFAULT_MODEL)

EVAL_PROVIDER = _get_role_setting("EVAL", "PROVIDER", DEFAULT_PROVIDER).strip()
EVAL_BASE_URL = _get_role_setting("EVAL", "API_BASE", DEFAULT_BASE_URL).rstrip("/")
EVAL_API_KEY = _get_role_setting("EVAL", "API_KEY", DEFAULT_API_KEY)
EVAL_MODEL = _get_role_setting("EVAL", "MODEL_NAME", DEFAULT_MODEL)

QA_PROVIDER = _get_role_setting("QA", "PROVIDER", DEFAULT_PROVIDER).strip()
QA_BASE_URL = _get_role_setting("QA", "API_BASE", DEFAULT_BASE_URL).rstrip("/")
QA_API_KEY = _get_role_setting("QA", "API_KEY", DEFAULT_API_KEY)
QA_MODEL = _get_role_setting("QA", "MODEL_NAME", DEFAULT_MODEL)


def _qualify_model_name(model: str, provider: str) -> str:
    if "/" in model:
        return model
    return f"{provider}/{model}"


def get_local_llm(
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    provider: str = DEFAULT_PROVIDER,
    base_url: str = DEFAULT_BASE_URL,
    api_key: str = DEFAULT_API_KEY,
):
    """Return an environment-driven LLM config for local OpenAI-compatible backends."""
    return LLM(
        model=_qualify_model_name(model, provider),
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
    )


def get_keck_llm(model: str = WORKER_MODEL):
    """Backward-compatible wrapper used by the existing agent factory modules."""
    return get_local_llm(
        model=model,
        provider=WORKER_PROVIDER,
        base_url=WORKER_BASE_URL,
        api_key=WORKER_API_KEY,
    )


def get_keck_eval_llm():
    return get_local_llm(
        model=EVAL_MODEL,
        temperature=0.0,
        provider=EVAL_PROVIDER,
        base_url=EVAL_BASE_URL,
        api_key=EVAL_API_KEY,
    )


def get_manager_llm():
    return get_local_llm(
        model=MANAGER_MODEL,
        temperature=0.1,
        provider=MANAGER_PROVIDER,
        base_url=MANAGER_BASE_URL,
        api_key=MANAGER_API_KEY,
    )


def get_qa_llm():
    return get_local_llm(
        model=QA_MODEL,
        temperature=0.0,
        provider=QA_PROVIDER,
        base_url=QA_BASE_URL,
        api_key=QA_API_KEY,
    )
