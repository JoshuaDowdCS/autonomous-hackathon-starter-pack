# DeepSeek-V3 DGX Deployment

This repo now includes a local-only deployment path for a DGX-style box:

- `docker-compose.yml` starts vLLM, Qdrant, Ollama, Redis, the agent API, and the Vite frontend.
- `Dockerfile.agents` builds the CrewAI orchestration container with Python and Node runtime support.
- `pipeline/api.py` exposes `GET /health`, `GET /status/{key}`, and `POST /run`.

## Boot

```bash
cp .env.example .env
mkdir -p "${SCRATCH_ROOT:-./.runtime}"
docker compose up --build -d
```

## Verify

```bash
curl http://localhost:11434/v1/models
curl http://localhost:8001/health
curl http://localhost:5173
```

## Run the Crew

```bash
curl -X POST http://localhost:8001/run \
  -H 'Content-Type: application/json' \
  -d '{
    "data_source": "data/sample.csv",
    "project_description": "Build a real-time collaborative code editor",
    "data_strategy": "local"
  }'
```

## Notes

- The agent service is wired for 10 CrewAI agents plus a hierarchical manager LLM.
- Shared memory is best-effort. Redis caching is used immediately; Mem0/Qdrant/Ollama are initialized when available.
- `OPENAI_MODEL_NAME` must match the vLLM `--served-model-name`.
