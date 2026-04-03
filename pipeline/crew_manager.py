import os

from crewai import Crew, Process, Task
from pipeline.agents.llm_config import get_manager_llm
from pipeline.prompting import build_profiler_lenses, build_project_context, get_output_schema

from pipeline.agents.data_layer import (
    get_data_loader_agent,
    get_validator_agent,
    get_analyzer_agent,
    get_web_scraper_agent,
)
from pipeline.agents.delivery_layer import get_documentation_agent
from pipeline.agents.user_layer import get_profiler_agent, get_interpreter_agent, get_formatter_agent
from pipeline.agents.ui_layer import get_qa_agent, get_code_fixer_agent
from pipeline.agents.eval_layer import get_eval_agent


def run_crew_pipeline(
    data_source: str,
    project_description: str,
    data_strategy: str = "local",
    memory_context: str = "",
):
    manager_llm = get_manager_llm()
    project_context = build_project_context(
        project_description=project_description,
        data_source=data_source,
        data_strategy=data_strategy,
        memory_context=memory_context,
    )
    output_schema = get_output_schema()
    profiler_lenses = build_profiler_lenses()
    enable_ui_qa = os.getenv("ENABLE_UI_QA", "false").lower() == "true"
    enable_codex_fixer = os.getenv("ENABLE_CODEX_FIXER", "false").lower() == "true"
    
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
    eval_agent = get_eval_agent()
    documentation_agent = get_documentation_agent()
    qa_agent = get_qa_agent() if enable_ui_qa else None
    code_fixer = get_code_fixer_agent() if enable_codex_fixer else None

    # 2. Define simple tasks for the pipeline
    task_load = Task(
        description=(
            f"Load the implementation brief or supporting material from: {data_source}\n\n"
            f"{project_context}"
        ),
        expected_output='Relevant project source material correctly ingested into the database.',
        agent=data_loader
    )
    
    task_validate = Task(
        description=(
            "Validate the ingested project material for missing requirements, contradictions, and unusable content. "
            "Preserve concrete implementation constraints.\n\n"
            f"{project_context}"
        ),
        expected_output='A clean, trustworthy implementation input set with any gaps or assumptions called out.',
        agent=validator
    )
    
    task_analyze = Task(
        description=(
            "Produce structured implementation notes from the validated material. Cover user flow, session lifecycle, "
            "live camera handling, spoken feedback loop, storage, guardrails, and MVP scope.\n\n"
            f"{project_context}"
        ),
        expected_output='A structured implementation summary with concrete technical decisions and tradeoffs.',
        agent=analyzer
    )

    task_profile = Task(
        description=(
            f'Infer the target user and practice context for the project "{project_description}". '
            "Do not ask the human follow-up questions. Instead, derive a realistic profile, flag assumptions, and "
            "cover these lenses:\n"
            f"{profiler_lenses}\n\n"
            f"{project_context}"
        ),
        expected_output='A target-user profile with assumptions, environment constraints, and coaching expectations.',
        agent=profiler
    )
    
    task_interpret = Task(
        description=(
            "Merge the analyzed source material with the inferred user profile and produce an implementation blueprint. "
            "Make concrete choices for frontend architecture, backend orchestration, Gemini Live integration, prompt strategy, "
            "spoken coaching behavior, note persistence, and post-session learning summaries. Distinguish MVP choices from later upgrades.\n\n"
            f"{project_context}"
        ),
        expected_output='A product blueprint JSON with clear implementation choices and assumptions.',
        agent=interpreter
    )
    
    task_format = Task(
        description=(
            "Convert the internal JSON into the predefined output schema ready for the UI layer. "
            "Return valid JSON only and make every field implementation-ready.\n\n"
            f"Output schema:\n{output_schema}\n\n"
            f"{project_context}"
        ),
        expected_output='A valid JSON string that matches the configured schema exactly.',
        agent=formatter
    )

    task_eval = Task(
        description=(
            "Evaluate the formatted JSON output. Score out of 10 and fail if under 7. The plan must be feasible, "
            "specific, grounded in the brief, and cover live coaching flow, spoken feedback, note capture, and safety boundaries."
        ),
        expected_output='A pass/fail result with detailed reasoning and missing requirements if any.',
        agent=eval_agent
    )

    task_document = Task(
        description=(
            "Create concise delivery notes that summarize the final output, evaluation result, "
            "QA status, deployment assumptions, and top follow-up actions for the generated yoga coaching app."
        ),
        expected_output="A short deployment-ready summary with risks and next steps.",
        agent=documentation_agent,
    )

    # 3. Create Crew
    agents = [
        data_loader,
        validator,
        analyzer,
        profiler,
        interpreter,
        formatter,
        eval_agent,
        documentation_agent,
    ]
    tasks = [
        task_load,
        task_validate,
        task_analyze,
        task_profile,
        task_interpret,
        task_format,
        task_eval,
        task_document,
    ]

    if qa_agent:
        task_qa = Task(
            description='Invoke the Stagehand-driven UI QA runner to load the React app and confirm the output shows inside the expected selectors.',
            expected_output='Stagehand QA report describing any selector misses or a clean "Pass".',
            agent=qa_agent
        )
        agents.append(qa_agent)
        tasks.insert(-1, task_qa)

    if code_fixer:
        task_codex_fix = Task(
            description='If QA reports issues, use the Codex CLI to patch the source code and re-test.',
            expected_output='Source code patched and verified via final QA pass.',
            agent=code_fixer
        )
        agents.append(code_fixer)
        tasks.insert(-1, task_codex_fix)

    hackathon_crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.hierarchical,
        manager_llm=manager_llm,
        verbose=True
    )
    
    # Run the crew pipeline
    return hackathon_crew.kickoff(inputs={"topic": project_description})
