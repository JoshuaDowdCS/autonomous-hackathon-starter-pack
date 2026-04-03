from crewai import Agent
from .llm_config import get_keck_llm
from .tools import load_local_data_tool, fetch_api_data_tool, scrape_web_data_tool

def get_data_loader_agent():
    return Agent(
        role='Data Loader',
        goal='Load the project brief or reference material from a file path or URL and write it to the raw_data table.',
        backstory='Expert research engineer who gathers build context from local files and external sources, preserving product requirements for the downstream planning agents.',
        verbose=True,
        allow_delegation=False,
        tools=[load_local_data_tool, fetch_api_data_tool],
        llm=get_keck_llm()
    )

def get_validator_agent():
    return Agent(
        role='Data Validator',
        goal='Check the ingested source material for missing context, contradictions, and unusable content before planning begins.',
        backstory='Meticulous analyst who turns rough briefs and scraped references into dependable implementation inputs.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )

def get_analyzer_agent():
    return Agent(
        role='Data Analyzer',
        goal='Summarize the validated source material into structured implementation notes, product constraints, and key technical decisions.',
        backstory='Product-minded systems thinker who turns raw source material into actionable engineering direction.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )


def get_web_scraper_agent():
    return Agent(
        role='Web Scraper',
        goal='Scrape the requested URLs and persist only the text needed to support the implementation plan.',
        backstory='Scrutinous researcher who turns web pages into clean planning inputs while avoiding irrelevant noise.',
        verbose=True,
        allow_delegation=False,
        tools=[scrape_web_data_tool],
        llm=get_keck_llm()
    )
