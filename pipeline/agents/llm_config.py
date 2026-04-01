from crewai import LLM
import os

KECK_OLLAMA_URL = "http://localhost:11434"
KECK_DEFAULT_MODEL = "llama3.1:405b"
KECK_EVAL_MODEL = "llama3.1:70b"
KECK_QA_MODEL = "gpt-oss:20b"
KECK_MANAGER_MODEL = "llama3.1:405b"


def get_keck_llm(model: str = KECK_DEFAULT_MODEL):
    """Returns an LLM configured for the Keck Cluster's Ollama endpoint."""
    return LLM(
        model=model,
        base_url=KECK_OLLAMA_URL
    )


def get_keck_eval_llm():
    """Provide the evaluator with the Llama 3.1 70B checkpoint."""
    return get_keck_llm(model=KECK_EVAL_MODEL)

def get_manager_llm():
    """Route CrewAI orchestration through the local Llama 3.1 405B endpoint."""
    return get_keck_llm(model=KECK_MANAGER_MODEL)


def get_qa_llm():
    """Point UI QA and Codex tooling at the GPU-friendly GPT-OSS 20B checkpoint."""
    return get_keck_llm(model=KECK_QA_MODEL)
