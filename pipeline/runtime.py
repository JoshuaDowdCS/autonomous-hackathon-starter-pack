import hashlib
import json
import logging
import os
from typing import Any

from redis import Redis

try:
    from mem0 import Memory
except Exception:  # pragma: no cover - optional dependency path
    Memory = None

logger = logging.getLogger(__name__)


class HackathonMemoryManager:
    """Optional Redis + Mem0 backed memory for repeated orchestration runs."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.memory_user_id = os.getenv("MEMORY_USER_ID", "hackathon")
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.openai_api_base = os.getenv("OPENAI_API_BASE", "http://deepseek-vllm:8000/v1")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "dummy")
        self.openai_model_name = os.getenv("OPENAI_MODEL_NAME", "deepseek-v3")
        self.embedding_model_name = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.collection_name = os.getenv("MEMORY_COLLECTION_NAME", "hackathon_agents")
        self.redis_client = None
        self.memory = None

        self._init_redis()
        self._init_mem0()

    def _init_redis(self):
        try:
            self.redis_client = Redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis cache connected")
        except Exception as exc:
            logger.warning("Redis unavailable; continuing without cache: %s", exc)
            self.redis_client = None

    def _init_mem0(self):
        if Memory is None:
            logger.info("mem0 not installed; shared memory disabled")
            return

        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": self.openai_model_name,
                    "base_url": self.openai_api_base,
                    "api_key": self.openai_api_key,
                },
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": self.embedding_model_name,
                    "base_url": self.ollama_base_url,
                },
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "url": self.qdrant_url,
                    "collection_name": self.collection_name,
                },
            },
        }
        if self.qdrant_api_key:
            config["vector_store"]["config"]["api_key"] = self.qdrant_api_key

        try:
            self.memory = Memory.from_config(config)
            logger.info("Mem0 memory initialized")
        except Exception as exc:
            logger.warning("Mem0 unavailable; continuing without semantic memory: %s", exc)
            self.memory = None

    def _cache_key(self, project_description: str, data_source: str, data_strategy: str) -> str:
        raw = f"{project_description}|{data_source}|{data_strategy}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"hackathon_run:{digest}"

    def get_cached_run(self, project_description: str, data_source: str, data_strategy: str) -> dict[str, Any] | None:
        if not self.redis_client:
            return None
        key = self._cache_key(project_description, data_source, data_strategy)
        payload = self.redis_client.get(key)
        if not payload:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {"raw": payload}

    def set_cached_run(
        self,
        project_description: str,
        data_source: str,
        data_strategy: str,
        payload: dict[str, Any],
        ttl_seconds: int = 86400,
    ):
        if not self.redis_client:
            return
        key = self._cache_key(project_description, data_source, data_strategy)
        self.redis_client.setex(key, ttl_seconds, json.dumps(payload, default=str))

    def search_context(self, query: str, limit: int = 3) -> str:
        if not self.memory:
            return ""
        try:
            results = self.memory.search(query=query, user_id=self.memory_user_id, limit=limit)
        except TypeError:
            try:
                results = self.memory.search(query, user_id=self.memory_user_id, limit=limit)
            except Exception as exc:
                logger.warning("Memory search failed: %s", exc)
                return ""
        except Exception as exc:
            logger.warning("Memory search failed: %s", exc)
            return ""

        entries = []
        for item in results or []:
            if isinstance(item, dict):
                entry = (
                    item.get("memory")
                    or item.get("text")
                    or item.get("data", {}).get("memory")
                    or json.dumps(item)
                )
            else:
                entry = str(item)
            if entry:
                entries.append(entry)
        return "\n".join(entries)

    def remember_run(self, project_description: str, result: Any):
        if not self.memory:
            return
        message = (
            f"Project: {project_description}\n"
            f"Outcome summary: {str(result)[:4000]}"
        )
        try:
            self.memory.add(message, user_id=self.memory_user_id, metadata={"project": project_description})
        except TypeError:
            try:
                self.memory.add(
                    messages=[{"role": "user", "content": project_description}, {"role": "assistant", "content": str(result)[:4000]}],
                    user_id=self.memory_user_id,
                )
            except Exception as exc:
                logger.warning("Memory add failed: %s", exc)
        except Exception as exc:
            logger.warning("Memory add failed: %s", exc)
