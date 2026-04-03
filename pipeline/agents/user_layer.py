from crewai import Agent
from .llm_config import get_keck_llm

def get_profiler_agent():
    return Agent(
        role='User Profiler',
        goal='Infer the target user, environment, and coaching expectations from the project brief, and clearly label assumptions.',
        backstory='Product strategist who can derive realistic user needs from an early concept without inventing fake interview data.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )

def get_interpreter_agent():
    return Agent(
        role='Need Interpreter',
        goal='Merge the inferred user needs with the analyzed source material and produce a shippable product blueprint in JSON.',
        backstory='Applied product architect who translates ambiguous ideas into concrete system design, UX flows, and implementation priorities.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )

def get_formatter_agent():
    return Agent(
        role='Output Formatter',
        goal='Convert the implementation blueprint into strict schema-valid JSON with concrete build details and no markdown.',
        backstory='Meticulous engineer who produces machine-consumable JSON without losing important implementation detail.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )
