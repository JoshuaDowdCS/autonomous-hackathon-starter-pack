import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from db.state_store import get_state, init_db, set_state
from pipeline.crew_manager import run_crew_pipeline
from pipeline.runtime import HackathonMemoryManager

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

memory_manager = HackathonMemoryManager()


class RunRequest(BaseModel):
    data_source: str = Field(..., description="Local file path or URL for the pipeline input.")
    project_description: str = Field(..., description="High-level project objective for the crew.")
    data_strategy: str = Field(default="local", pattern="^(local|web)$")
    use_cache: bool = Field(default=True)


class RunResponse(BaseModel):
    status: str
    timestamp: str
    cached: bool = False
    result: Any


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    set_state("service", "ready", "API started")
    yield


app = FastAPI(title="Hackathon Orchestrator", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model": os.getenv("OPENAI_MODEL_NAME", "deepseek-v3"),
        "base_url": os.getenv("OPENAI_API_BASE", "http://deepseek-vllm:8000/v1"),
    }


@app.get("/status/{key}")
async def read_status(key: str):
    state = get_state(key)
    if state is None:
        raise HTTPException(status_code=404, detail=f"No state found for key '{key}'")
    return state


@app.post("/run", response_model=RunResponse)
async def run_pipeline_endpoint(request: RunRequest):
    init_db()
    set_state("pipeline", "running", request.project_description)

    if request.use_cache:
        cached = memory_manager.get_cached_run(
            request.project_description,
            request.data_source,
            request.data_strategy,
        )
        if cached is not None:
            set_state("pipeline", "complete", "Served from Redis cache")
            return RunResponse(
                status="complete",
                timestamp=datetime.utcnow().isoformat(),
                cached=True,
                result=cached,
            )

    try:
        memory_context = memory_manager.search_context(request.project_description, limit=3)
        result = run_crew_pipeline(
            request.data_source,
            request.project_description,
            request.data_strategy,
            memory_context=memory_context,
        )
        payload = {"crew_output": str(result)}
        memory_manager.set_cached_run(
            request.project_description,
            request.data_source,
            request.data_strategy,
            payload,
        )
        memory_manager.remember_run(request.project_description, result)
        set_state("pipeline", "complete", payload["crew_output"][:2000])
        return RunResponse(
            status="complete",
            timestamp=datetime.utcnow().isoformat(),
            result=payload,
        )
    except Exception as exc:
        logger.exception("Pipeline run failed")
        set_state("pipeline", "failed", str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
