import os
from functools import lru_cache

import yaml


ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")


def _load_yaml(filename: str) -> dict:
    path = os.path.join(ROOT_DIR, filename)
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache(maxsize=1)
def load_builder_config() -> dict:
    return _load_yaml("config.yaml")


@lru_cache(maxsize=1)
def load_profiler_questions() -> list[str]:
    payload = _load_yaml("profiler_questions.yaml")
    questions = payload.get("questions") or []
    return [question.strip() for question in questions if question and question.strip()]


def get_output_schema() -> str:
    return str(load_builder_config().get("output_schema", "")).strip()


def build_project_context(project_description: str, data_source: str, data_strategy: str, memory_context: str) -> str:
    lines = [
        f"Project brief: {project_description}",
        f"Source material: {data_source}",
        f"Source strategy: {data_strategy}",
        (
            "Treat this as a software implementation brief. The output must describe how to build a working product, "
            "not just analyze source data."
        ),
        (
            "The target product is a yoga form coach web app that watches live camera input, uses the Gemini Live API "
            "for real-time multimodal coaching, speaks back short corrective cues, and stores end-of-session notes."
        ),
        (
            "Keep recommendations feasible for a hackathon MVP, but note the production-grade follow-up work needed "
            "around latency, safety, privacy, and session orchestration."
        ),
        f"Relevant prior context:\n{memory_context or 'No prior shared memory available.'}",
    ]
    return "\n\n".join(lines)


def build_profiler_lenses() -> str:
    questions = load_profiler_questions()
    if not questions:
        return "Infer the target user, environment, and coaching expectations from the brief."
    return "\n".join(f"- {question}" for question in questions)
