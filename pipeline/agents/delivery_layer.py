from crewai import Agent

from .llm_config import get_keck_llm


def get_documentation_agent():
    return Agent(
        role="Documentation Lead",
        goal="Capture the final implementation, operational notes, and follow-up actions for the team.",
        backstory=(
            "Technical writer embedded in the hackathon team who turns agent outputs "
            "into concise delivery notes, assumptions, and next steps."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm(),
    )
