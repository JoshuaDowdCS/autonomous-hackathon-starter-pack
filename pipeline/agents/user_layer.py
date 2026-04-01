from crewai import Agent
from .llm_config import get_keck_llm, get_qa_llm

def get_profiler_agent():
    return Agent(
        role='User Profiler',
        goal='Ask 5-8 questions based on project topic and store answers in user_profile.',
        backstory='Expert conversationalist who easily extracts technical needs and preferences from end users.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )

def get_interpreter_agent():
    return Agent(
        role='Need Interpreter',
        goal='Read user profile and analyzed data to produce match and insight JSON.',
        backstory='Analytical psychologist skilled at bridging the gap between raw data and specific user workflows.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )

def get_formatter_agent():
    return Agent(
        role='Output Formatter',
        goal='Convert interpreter JSON to a final UI-ready format that perfectly matches the output schema.',
        backstory='Meticulous frontend engineer who ensures API responses match strict JSON schemas.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )
