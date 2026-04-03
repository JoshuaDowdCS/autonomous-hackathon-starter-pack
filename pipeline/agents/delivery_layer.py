from crewai import Agent

from .llm_config import get_keck_llm


def get_documentation_agent():
    return Agent(
        role="Documentation Lead",
        goal="Capture the final implementation summary, operational caveats, and next steps for shipping the generated product.",
        backstory=(
            "Technical writer embedded in the hackathon team who turns implementation plans "
            "into concise delivery notes, assumptions, and launch follow-ups."
        ),
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm(),
    )
