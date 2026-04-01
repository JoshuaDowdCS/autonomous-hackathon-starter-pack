from crewai import Agent
from .llm_config import get_keck_eval_llm

def get_eval_agent():
    return Agent(
        role='Output Evaluator',
        goal='Score formatter output on factual grounding (0-5) and relevance (0-5). Fail if < 7/10 combined. Re-route to interpreter if failed.',
        backstory='Strict adjudicator ensuring only high-quality outputs reach the UI.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_eval_llm()
    )
