# Model Choices

The repo is now wired for a split local serving layout.

## Default serving topology

- `deepseek-vllm` serves `deepseek-r1-distill-llama-70b` on GPUs `1,2,4,5`
- `llama-vllm` serves `llama-3.3-70b-instruct` on GPUs `6,7`
- `ollama` serves the embedding model for shared memory
- `qdrant` stores vectors for Mem0

## Role routing

`pipeline/agents/llm_config.py` supports per-role endpoint and model routing:

- worker agents use `OPENAI_WORKER_API_BASE` and `OPENAI_WORKER_MODEL_NAME`
- manager uses `OPENAI_MANAGER_API_BASE` and `OPENAI_MANAGER_MODEL_NAME`
- evaluator uses `OPENAI_EVAL_API_BASE` and `OPENAI_EVAL_MODEL_NAME`
- QA/code-fix agents use `OPENAI_QA_API_BASE` and `OPENAI_QA_MODEL_NAME`

`pipeline/runtime.py` also supports separate memory LLM routing through:

- `OPENAI_MEMORY_API_BASE`
- `OPENAI_MEMORY_MODEL_NAME`

## Shipped defaults

The checked-in `.env.example` config defaults to:

- Llama 3.3 70B for worker, QA, and memory LLM traffic
- DeepSeek for manager and evaluator traffic
- Ollama `nomic-embed-text` for embeddings

## Operational note

The Docker stack now supports true multi-endpoint routing inside the app, but it still assumes one model per serving container by default:

- one DeepSeek service
- one Llama service

If you later want multiple DeepSeek or Llama instances, more advanced load balancing, or different GPU splits, that becomes a deployment-planning step rather than an application wiring step.
