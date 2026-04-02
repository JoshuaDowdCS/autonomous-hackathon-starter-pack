# Local model choices

This project now routes every Crew agent through your local Ollama endpoint rather than cloud APIs. The choices below pair each agent group with the most fitting locally hosted checkpoint.

## Llama 3.1 8B (primary pipeline + QA)
- get_keck_llm() now defaults to `llama3.1:8b`, so the data loader, validator, analyzer, profiler, interpreter, formatter, and delivery agents run on a faster, lighter checkpoint. See pipeline/agents/data_layer.py:5-45, pipeline/agents/user_layer.py:4-32, pipeline/agents/delivery_layer.py:1-19, and pipeline/agents/llm_config.py:4-45.
- The UI QA agent also points to `llama3.1:8b` by default so interactive checks stay responsive.

## DeepSeek V3 (manager + evaluator)
- `OPENAI_MANAGER_MODEL_NAME` and `OPENAI_EVAL_MODEL_NAME` default to `deepseek-v3` so the orchestrator and evaluator still use the heavyweight checkpoint for harder planning or scoring passes.

Together these choices keep most tasks fast while preserving DeepSeek for heavy reasoning; override the `OPENAI_*_MODEL_NAME` environment variables if you want different checkpoints.
