import os

from crewai import LLM

LOCAL_LLM_PROVIDER = os.getenv("LOCAL_LLM_PROVIDER", "openai").strip()
LOCAL_LLM_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1").rstrip("/")
LOCAL_LLM_API_KEY = os.getenv("OPENAI_API_KEY", "dummy")
LOCAL_LLM_DEFAULT_MODEL = os.getenv("OPENAI_MODEL_NAME", "deepseek-v3")
LOCAL_LLM_EVAL_MODEL = os.getenv("OPENAI_EVAL_MODEL_NAME", LOCAL_LLM_DEFAULT_MODEL)
LOCAL_LLM_QA_MODEL = os.getenv("OPENAI_QA_MODEL_NAME", LOCAL_LLM_DEFAULT_MODEL)
LOCAL_LLM_MANAGER_MODEL = os.getenv("OPENAI_MANAGER_MODEL_NAME", LOCAL_LLM_DEFAULT_MODEL)
LOCAL_LLM_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))


def _qualify_model_name(model: str) -> str:
    if "/" in model:
        return model
    return f"{LOCAL_LLM_PROVIDER}/{model}"


def get_local_llm(model: str = LOCAL_LLM_DEFAULT_MODEL, temperature: float = LOCAL_LLM_TEMPERATURE):
    """Return an environment-driven LLM config for local OpenAI-compatible backends."""
    return LLM(
        model=_qualify_model_name(model),
        base_url=LOCAL_LLM_BASE_URL,
        api_key=LOCAL_LLM_API_KEY,
        temperature=temperature,
    )


def get_keck_llm(model: str = LOCAL_LLM_DEFAULT_MODEL):
    """Backward-compatible wrapper used by the existing agent factory modules."""
    return get_local_llm(model=model)


def get_keck_eval_llm():
    return get_local_llm(model=LOCAL_LLM_EVAL_MODEL, temperature=0.0)


def get_manager_llm():
    return get_local_llm(model=LOCAL_LLM_MANAGER_MODEL, temperature=0.1)


def get_qa_llm():
    return get_local_llm(model=LOCAL_LLM_QA_MODEL, temperature=0.0)
