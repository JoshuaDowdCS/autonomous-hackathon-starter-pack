from crewai import Agent
from .llm_config import get_qa_llm
from .tools import codex_patch_tool, codex_rewrite_tool, stagehand_ui_qa_tool

def get_formatter_agent():
    return Agent(
        role='Formatter',
        goal='Use codex rewrite to transform Interpreter JSON into UI-ready components.',
        backstory='Expert developer who translates structured JSON into React components using Codex CLI.',
        verbose=True,
        allow_delegation=False,
        tools=[codex_rewrite_tool],
        llm=get_qa_llm()
    )

def get_qa_agent():
    return Agent(
        role='UI QA Agent',
        goal='Invoke the Stagehand QA runner script to load the UI, confirm key selectors render, and report the findings.',
        backstory='Expert QA engineer who automates browser checks with Stagehand-powered scripts and clearly summarizes regressions.',
        verbose=True,
        allow_delegation=False,
        tools=[stagehand_ui_qa_tool],
        llm=get_qa_llm()
    )

def get_code_fixer_agent():
    return Agent(
        role='Code Fixer',
        goal='Read QA reports and use Codex CLI to patch the broken code with a max of 3 retries.',
        backstory='10x frontend developer who patches UI issues lighting fast.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        tools=[codex_patch_tool],
        llm=get_qa_llm()
    )
