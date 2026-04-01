from crewai import Agent
from .llm_config import get_keck_llm
from .tools import load_local_data_tool, fetch_api_data_tool, scrape_web_data_tool

def get_data_loader_agent():
    return Agent(
        role='Data Loader',
        goal='Load data from file path or API URL and write to the raw_data table.',
        backstory='Expert data engineer specialized in extracting data from various sources quickly and reliably. You determine whether you are dealing with a local file path or an external URL API, and pick the right tool for the job. Once the tool succeeds, you return success.',
        verbose=True,
        allow_delegation=False,
        tools=[load_local_data_tool, fetch_api_data_tool],
        llm=get_keck_llm()
    )

def get_validator_agent():
    return Agent(
        role='Data Validator',
        goal='Check data schema, deduplicate, flag nulls, and ensure data quality.',
        backstory='Meticulous Quality Analyst dedicated to maintaining data integrity.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )

def get_analyzer_agent():
    return Agent(
        role='Data Analyzer',
        goal='Summarize raw data into structured JSON.',
        backstory='Insightful Data Scientist who creates concise and structured summaries of complex datasets.',
        verbose=True,
        allow_delegation=False,
        llm=get_keck_llm()
    )


def get_web_scraper_agent():
    return Agent(
        role='Web Scraper',
        goal='Scrape the requested URLs (falling back only if the HTML can be parsed) and persist the results to raw_data.',
        backstory='Scrutinous researcher who turns web pages into clean text blobs for downstream tasks. Choose selectors carefully, store the cleaned output, and report success.',
        verbose=True,
        allow_delegation=False,
        tools=[scrape_web_data_tool],
        llm=get_keck_llm()
    )
