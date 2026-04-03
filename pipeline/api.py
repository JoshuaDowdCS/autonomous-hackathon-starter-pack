import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

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
    project_description: str = Field(..., description="Implementation brief describing the product the builder should generate.")
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model": os.getenv("OPENAI_WORKER_MODEL_NAME", os.getenv("OPENAI_MODEL_NAME", "llama-3.3-70b-instruct")),
        "base_url": os.getenv("OPENAI_WORKER_API_BASE", os.getenv("OPENAI_API_BASE", "http://llama-vllm:8000/v1")),
        "backends": {
            "worker": {
                "model": os.getenv("OPENAI_WORKER_MODEL_NAME", os.getenv("OPENAI_MODEL_NAME", "llama-3.3-70b-instruct")),
                "base_url": os.getenv("OPENAI_WORKER_API_BASE", os.getenv("OPENAI_API_BASE", "http://llama-vllm:8000/v1")),
            },
            "manager": {
                "model": os.getenv("OPENAI_MANAGER_MODEL_NAME", os.getenv("OPENAI_MODEL_NAME", "llama-3.3-70b-instruct")),
                "base_url": os.getenv("OPENAI_MANAGER_API_BASE", os.getenv("OPENAI_API_BASE", "http://llama-vllm:8000/v1")),
            },
            "eval": {
                "model": os.getenv("OPENAI_EVAL_MODEL_NAME", os.getenv("OPENAI_MODEL_NAME", "llama-3.3-70b-instruct")),
                "base_url": os.getenv("OPENAI_EVAL_API_BASE", os.getenv("OPENAI_API_BASE", "http://llama-vllm:8000/v1")),
            },
            "qa": {
                "model": os.getenv("OPENAI_QA_MODEL_NAME", os.getenv("OPENAI_MODEL_NAME", "llama-3.3-70b-instruct")),
                "base_url": os.getenv("OPENAI_QA_API_BASE", os.getenv("OPENAI_API_BASE", "http://llama-vllm:8000/v1")),
            },
            "memory": {
                "model": os.getenv("OPENAI_MEMORY_MODEL_NAME", os.getenv("OPENAI_WORKER_MODEL_NAME", os.getenv("OPENAI_MODEL_NAME", "llama-3.3-70b-instruct"))),
                "base_url": os.getenv("OPENAI_MEMORY_API_BASE", os.getenv("OPENAI_WORKER_API_BASE", os.getenv("OPENAI_API_BASE", "http://llama-vllm:8000/v1"))),
            },
            "embedder": {
                "model": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
            },
            "vector_store": {
                "url": os.getenv("QDRANT_URL", "http://qdrant:6333"),
            },
        },
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
