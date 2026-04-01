from crewai import Crew, Process, Task
from pipeline.agents.llm_config import get_manager_llm

from pipeline.agents.data_layer import (
    get_data_loader_agent,
    get_validator_agent,
    get_analyzer_agent,
    get_web_scraper_agent,
)
from pipeline.agents.user_layer import get_profiler_agent, get_interpreter_agent, get_formatter_agent
from pipeline.agents.ui_layer import get_qa_agent, get_code_fixer_agent
from pipeline.agents.eval_layer import get_eval_agent

def run_crew_pipeline(data_source: str, project_description: str, data_strategy: str = "local"):
    manager_llm = get_manager_llm()
    
    # 1. Instantiate agents
    if data_strategy.lower() == "web":
        data_loader = get_web_scraper_agent()
    else:
        data_loader = get_data_loader_agent()
    validator = get_validator_agent()
    analyzer = get_analyzer_agent()
    
    profiler = get_profiler_agent()
    interpreter = get_interpreter_agent()
    formatter = get_formatter_agent()
    
    # UI and Coding Agents
    qa_agent = get_qa_agent()
    code_fixer = get_code_fixer_agent()
    
    eval_agent = get_eval_agent()

    # 2. Define simple tasks for the pipeline
    task_load = Task(
        description=f'Load the data from source: {data_source}',
        expected_output='Raw data correctly ingested into the database.',
        agent=data_loader
    )
    
    task_validate = Task(
        description='Validate the ingested raw data for consistency and schema compliance.',
        expected_output='A clean and valid database table containing raw data.',
        agent=validator
    )
    
    task_analyze = Task(
        description='Produce a structured JSON summary from the validated raw data.',
        expected_output='A JSON object containing the generalized data summary.',
        agent=analyzer
    )

    task_profile = Task(
        description=f'Based on the project topic "{project_description}", ask 5-8 questions to profile the target user.',
        expected_output='A comprehensive user profile outlining needs and goals.',
        agent=profiler
    )
    
    task_interpret = Task(
        description='Merge the generated user profile with the insights to produce customized actionable data.',
        expected_output='A personalized insights JSON based strictly on the user profile.',
        agent=interpreter
    )
    
    task_format = Task(
        description='Convert the internal JSON into the predefined output schema ready for the UI layer.',
        expected_output='A perfectly formatted schema-matching JSON string.',
        agent=formatter
    )

    task_eval = Task(
        description='Evaluate the formatted JSON output. Score out of 10. Fail if under 7.',
        expected_output='A pass/fail boolean result with detailed reasoning.',
        agent=eval_agent
    )

    task_qa = Task(
        description='Invoke the Stagehand-driven UI QA runner to load the React app and confirm the output shows inside the expected selectors.',
        expected_output='Stagehand QA report describing any selector misses or a clean "Pass".',
        agent=qa_agent
    )

    task_codex_fix = Task(
        description='If QA reports issues, use the Codex CLI to patch the source code and re-test.',
        expected_output='Source code patched and verified via final QA pass.',
        agent=code_fixer
    )

    # 3. Create Crew
    hackathon_crew = Crew(
        agents=[data_loader, validator, analyzer, profiler, interpreter, formatter, eval_agent, qa_agent, code_fixer],
        tasks=[task_load, task_validate, task_analyze, task_profile, task_interpret, task_format, task_eval, task_qa, task_codex_fix],
        process=Process.hierarchical,
        manager_llm=manager_llm,
        verbose=True
    )
    
    # Run the crew pipeline
    return hackathon_crew.kickoff(inputs={"topic": project_description})
