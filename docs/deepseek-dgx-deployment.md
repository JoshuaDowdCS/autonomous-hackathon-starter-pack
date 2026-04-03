# DGX Deployment

This repo now assumes a split local serving stack on a GPU server:

- `deepseek-vllm` for manager and evaluator traffic
- `llama-vllm` for worker and QA traffic
- `ollama` for embeddings
- `qdrant` for vector storage
- `redis` for caching

## Boot

```bash
./bootstrap.sh up
```

## Verify

```bash
curl http://localhost:8000/v1/models
curl http://localhost:8002/v1/models
curl http://localhost:8001/health
curl http://localhost:5173
```

## Run the crew

```bash
curl -X POST http://localhost:8001/run \
  -H 'Content-Type: application/json' \
  -d '{
    "data_source": "data/yoga_form_coach_brief.md",
    "project_description": "Build an at-home yoga form coach web app that uses the Gemini Live API to watch a user's live session, deliver spoken form cues through the user's active audio output, and save notes on what they did well, what to keep working on, and what they learned.",
    "data_strategy": "local",
    "use_cache": true
  }'
```

## Notes

- The default GPU split in `.env.example` is GPUs `1,2,4,5` for DeepSeek R1 Distill 70B and GPUs `6,7` for Llama 3.3 70B.
- The app is now aware of different endpoints for worker, manager, evaluator, QA, memory LLM, embedding, and vector-store traffic.
- `QDRANT_API_KEY` is optional for isolated local deployments.
- The browser UI uses the same backend `POST /run` path as the curl example.
