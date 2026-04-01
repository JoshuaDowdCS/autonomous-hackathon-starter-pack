# Local model choices

This project now routes every Crew agent through your local Ollama endpoint rather than cloud APIs. The choices below pair each agent group with the most fitting locally hosted checkpoint.

## Llama 3.1 405B (primary pipeline & manager)
- get_keck_llm() now defaults to llama3.1:405b, so the data loader, validator, analyzer, profiler, interpreter, formatter, and the Crew manager all share the same massive 405B reasoning stack. See pipeline/agents/data_layer.py:5-45, pipeline/agents/user_layer.py:4-32, and pipeline/agents/llm_config.py:4-37. This model is Meta's flagship open source checkpoint with 405 billion parameters and a 128K token context window, which gives the pipeline the richest grounding in long-form reasoning, tool use, and multilingual synthesis before the UI layer ever sees output. citeturn0news12
- Routing both the manager and these data/user tasks through an identical checkpoint keeps every agent consistent and lets the six GPUs stay focused on a single, heavyweight serving graph.

## Llama 3.1 70B (evaluator)
- pipeline/agents/eval_layer.py:4-12 calls get_keck_eval_llm(), which points at llama3.1:70b. The smaller 70B variant uses the same architecture and a generous context window but fits in far less memory, so the evaluator can score output quickly without reloading the entire 405B weights. citeturn0news12

## GPT-OSS 20B (QA + Codex fixer)
- The UI QA agent and the Codex patch tool rely on get_qa_llm() pointing to gpt-oss:20b (pipeline/agents/ui_layer.py:5-37). This OpenAI open-weight checkpoint is quantized for MXFP4 and only needs ~16GB of VRAM per GPU, keeping the interactive QA/code-fixing loop responsive while remaining fully local. citeturn1search3

Together these choices let you run everything on your on-prem Ollama container bound to the six GPUs you expose; swap the constants in pipeline/agents/llm_config.py and run ollama pull again if the hardware profile changes later.
