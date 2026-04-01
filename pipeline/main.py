import yaml
import os

from db.state_store import set_state
from pipeline.crew_manager import run_crew_pipeline

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_pipeline(data_source: str, project_description: str, data_strategy: str):
    print(f"Starting pipeline for project: {project_description}")
    print(f"Data source: {data_source}")
    print(f"Data strategy: {data_strategy}")
    
    set_state("pipeline", "running", "Pipeline started")
    
    # Run the Crew AI manager to route requests
    try:
        result = run_crew_pipeline(data_source, project_description, data_strategy)
        set_state("pipeline", "complete", str(result))
        print("Pipeline execution completed successfully.")
    except Exception as e:
        set_state("pipeline", "failed", str(e))
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    config = load_config()
    source = config.get("data_source", {}).get("file_path") or config.get("data_source", {}).get("url")
    desc = config.get("project_description", "Default Project")
    strategy = config.get("data_strategy", "local")
    run_pipeline(source, desc, strategy)
