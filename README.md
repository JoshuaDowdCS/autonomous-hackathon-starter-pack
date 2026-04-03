# Hackathon Orchestrator

This repo runs a CrewAI-based agent pipeline behind a FastAPI service and ships a small React UI for submitting implementation briefs.

The `OPENAI_*` environment variables in this project are used for OpenAI-compatible local endpoints. On a DGX or similar Linux server, that means local vLLM services, not a cloud OpenAI dependency.

## Server prerequisites

For the full Docker path on a Linux GPU server, make sure the host already has:

- Docker Engine with the Compose plugin
- a running Docker daemon
- NVIDIA drivers installed and working on the host
- NVIDIA Container Toolkit configured so Docker can see the GPUs
- enough local disk for model downloads, Ollama models, Redis/Qdrant data, and logs

This repo assumes the vLLM containers can access NVIDIA GPUs directly.

## What you can do now

- Start the backend agent service.
- Open the frontend at `http://localhost:5173`.
- Enter a product brief, data source, and strategy.
- Start the builder from the browser or by calling the API directly.

## Quick start with Docker

1. Copy the environment file:

```bash
cp .env.example .env
mkdir -p .runtime
```

2. Start the stack:

```bash
./bootstrap.sh up
```

3. Open:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8001/health`
- Backend docs: `http://localhost:8001/docs`

The script also:

- creates `.env` from `.env.example` if needed
- creates the runtime directories under `.runtime` or `SCRATCH_ROOT`
- starts the Docker services in a safe order
- starts both the DeepSeek and Llama vLLM services
- pulls the configured Ollama embedding model before the agent API starts

Other useful commands:

```bash
./bootstrap.sh status
./bootstrap.sh logs
./bootstrap.sh down
```

## First boot expectations

The first `./bootstrap.sh up` can take a long time on a fresh server because it may need to:

- build the frontend and agent images
- download the DeepSeek model for vLLM
- download the Llama 3.3 70B model for vLLM
- pull the Ollama image and the configured embedding model
- initialize Redis, Qdrant, and runtime storage

On a DGX-class machine this is normal. A slow first boot is expected; later restarts should be much faster.

## Local development

1. Install backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

2. Install frontend dependencies:

```bash
cd ui
npm ci
cd ..
```

3. Seed the SQLite database:

```bash
python3 -c "from db.state_store import init_db; init_db()"
```

4. Start the backend:

```bash
uvicorn pipeline.api:app --host 0.0.0.0 --port 8001
```

5. Start the frontend in another shell:

```bash
cd ui
npm run dev -- --host 0.0.0.0 --port 5173
```

## How to give it a project idea

The browser UI now posts directly to `POST /run`.

You can also call the API yourself:

```bash
curl -X POST http://localhost:8001/run \
  -H 'Content-Type: application/json' \
  -d '{
    "data_source": "data/sample.csv",
    "project_description": "Build an at-home yoga form coach web app that uses the Gemini Live API to watch a user's live session, deliver spoken form cues through the user's active audio output, and save notes on what they did well, what to keep working on, and what they learned.",
    "data_strategy": "local",
    "use_cache": true
  }'
```

`project_description` is the implementation brief. `data_source` can be a local file path or a URL. `data_strategy` should be `local` for files and `web` for scraping.

## Alternate CLI entrypoint

If you want to run without the API, update `config.yaml` and run:

```bash
python3 -m pipeline.main
```

## Current architecture

- `pipeline/api.py` exposes the backend service.
- `pipeline/crew_manager.py` builds and kicks off the CrewAI workflow.
- `ui/src/App.jsx` provides the browser control surface.
- `db/state_store.py` stores raw data and pipeline state in SQLite.

## Model routing today

The repo is now wired for two local OpenAI-compatible model endpoints plus a local embedding/vector stack:

- `deepseek-vllm` for reasoning-heavy manager and evaluator work
- `llama-vllm` for worker and QA traffic
- `ollama` for embeddings
- `qdrant` for vector storage

The code supports separate model names and endpoints by role:

- `OPENAI_MODEL_NAME` for most worker agents
- `OPENAI_WORKER_API_BASE` and `OPENAI_WORKER_MODEL_NAME` for worker agents
- `OPENAI_MANAGER_MODEL_NAME` for the hierarchical manager
- `OPENAI_MANAGER_API_BASE` and `OPENAI_MANAGER_MODEL_NAME` for the manager
- `OPENAI_EVAL_MODEL_NAME` for the evaluator
- `OPENAI_EVAL_API_BASE` and `OPENAI_EVAL_MODEL_NAME` for the evaluator
- `OPENAI_QA_MODEL_NAME` for QA/code-fix agents
- `OPENAI_QA_API_BASE` and `OPENAI_QA_MODEL_NAME` for QA/code-fix agents
- `OPENAI_MEMORY_API_BASE` and `OPENAI_MEMORY_MODEL_NAME` for Mem0's LLM layer

As shipped today, the Docker defaults route:

- workers, QA, and memory LLM traffic to the local Llama 3.3 70B endpoint on GPUs `6,7`
- manager and evaluator to the local DeepSeek endpoint
- memory embeddings to Ollama and vectors to Qdrant

## Network exposure

The Docker Compose file currently publishes several service ports to the host:

- `5173` for the frontend
- `8001` for the FastAPI orchestrator
- `8000` for the local DeepSeek vLLM endpoint
- `8002` for the local Llama vLLM endpoint
- `6333` and `6334` for Qdrant
- `6379` for Redis
- `11434` for Ollama

That is convenient for debugging, but it is not the most isolated layout. For a more locked-down internal deployment, keep only the ports you actually need exposed and leave the rest on the private Docker network.

## Notes

- The default sample input lives at `data/sample.csv`.
- Redis/Qdrant/Ollama-backed memory is best-effort. If those services are unavailable, the API still runs, but shared memory and caching features degrade.
- Qdrant runs locally in Docker by default. `QDRANT_API_KEY` is optional and can stay empty for an isolated internal deployment.
- The Stagehand QA and Codex patch tooling are optional follow-on steps for the UI-related agents. Enable them with `ENABLE_UI_QA=true` and `ENABLE_CODEX_FIXER=true` after those dependencies are available.
