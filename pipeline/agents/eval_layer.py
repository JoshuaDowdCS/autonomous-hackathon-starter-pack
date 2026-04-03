from crewai import Agent
from .llm_config import get_keck_eval_llm

def get_eval_agent():
    return Agent(
        role='Output Evaluator',
        goal='Score output on feasibility, grounding, completeness, and product fit. Fail if the plan misses key live coaching, audio, note-taking, or safety requirements.',
        backstory='Strict technical reviewer who blocks vague plans and only approves implementation-ready output.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_eval_llm()
    )
