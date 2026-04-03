#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
ENV_FILE="$REPO_ROOT/.env"
ENV_EXAMPLE="$REPO_ROOT/.env.example"
DEFAULT_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS:-1800}"

compose_cmd=()

log() {
  printf '[hackathon] %s\n' "$*"
}

fail() {
  printf '[hackathon] ERROR: %s\n' "$*" >&2
  exit 1
}

detect_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    compose_cmd=(docker compose)
    return
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    compose_cmd=(docker-compose)
    return
  fi

  fail "Docker Compose is required but was not found."
}

compose() {
  "${compose_cmd[@]}" "$@"
}

load_env_file() {
  if [[ ! -f "$ENV_FILE" ]]; then
    if [[ ! -f "$ENV_EXAMPLE" ]]; then
      fail "Missing both .env and .env.example."
    fi
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    log "Created .env from .env.example"
  fi

  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
}

ensure_runtime_dirs() {
  local runtime_root="${SCRATCH_ROOT:-$REPO_ROOT/.runtime}"

  if [[ "$runtime_root" != /* ]]; then
    runtime_root="$REPO_ROOT/${runtime_root#./}"
  fi

  mkdir -p \
    "$runtime_root/vllm_cache" \
    "$runtime_root/vllm_logs" \
    "$runtime_root/llama_vllm_logs" \
    "$runtime_root/qdrant_data" \
    "$runtime_root/qdrant_snapshots" \
    "$runtime_root/ollama_models" \
    "$runtime_root/redis_data" \
    "$runtime_root/agent_logs" \
    "$runtime_root/agent_workdir"

  log "Prepared runtime directories under $runtime_root"
}

require_command() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || fail "Required command '$cmd' was not found."
}

require_docker_daemon() {
  docker info >/dev/null 2>&1 || fail "Docker is installed but the daemon is not running."
}

wait_for_http() {
  local url="$1"
  local label="$2"
  local timeout_seconds="${3:-$DEFAULT_TIMEOUT_SECONDS}"
  local elapsed=0

  while (( elapsed < timeout_seconds )); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log "$label is ready: $url"
      return 0
    fi
    sleep 5
    elapsed=$((elapsed + 5))
  done

  fail "Timed out waiting for $label at $url"
}

wait_for_container_state() {
  local container_name="$1"
  local label="$2"
  local timeout_seconds="${3:-$DEFAULT_TIMEOUT_SECONDS}"
  local elapsed=0
  local state=""

  while (( elapsed < timeout_seconds )); do
    state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_name" 2>/dev/null || true)"
    if [[ "$state" == "healthy" || "$state" == "running" ]]; then
      log "$label is $state"
      return 0
    fi
    sleep 5
    elapsed=$((elapsed + 5))
  done

  fail "Timed out waiting for $label ($container_name). Last known state: ${state:-unknown}"
}

pull_ollama_embed_model() {
  local model_name="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"
  log "Ensuring Ollama embedding model is present: $model_name"
  compose exec -T ollama ollama pull "$model_name"
}

start_stack() {
  require_command curl
  require_command docker
  detect_compose
  require_docker_daemon
  load_env_file
  ensure_runtime_dirs

  log "DeepSeek model ${DEEPSEEK_MODEL_ID:-deepseek-ai/DeepSeek-R1-Distill-Llama-70B} on GPUs ${DEEPSEEK_CUDA_VISIBLE_DEVICES:-0,1}"
  log "Llama model ${LLAMA_MODEL_ID:-meta-llama/Llama-3.3-70B-Instruct} on GPUs ${LLAMA_CUDA_VISIBLE_DEVICES:-2,4}"

  log "Building and starting core services"
  compose up --build -d qdrant redis ollama frontend deepseek-vllm llama-vllm

  wait_for_container_state "qdrant_memory_db" "Qdrant"
  wait_for_container_state "redis_cache" "Redis"
  wait_for_container_state "ollama_embeddings" "Ollama"
  wait_for_http "http://127.0.0.1:5173" "Frontend"
  wait_for_http "http://127.0.0.1:${DEEPSEEK_HOST_PORT:-8000}/v1/models" "DeepSeek vLLM"
  wait_for_http "http://127.0.0.1:${LLAMA_HOST_PORT:-8002}/v1/models" "Llama vLLM"

  pull_ollama_embed_model

  log "Starting orchestrator"
  compose up --build -d agent-orchestrator

  wait_for_http "http://127.0.0.1:8001/health" "Agent API"

  log "Stack is ready."
  log "Frontend: http://127.0.0.1:5173"
  log "Backend health: http://127.0.0.1:8001/health"
  log "Backend docs: http://127.0.0.1:8001/docs"
  log "DeepSeek endpoint: http://127.0.0.1:${DEEPSEEK_HOST_PORT:-8000}/v1"
  log "Llama endpoint: http://127.0.0.1:${LLAMA_HOST_PORT:-8002}/v1"
}

stop_stack() {
  detect_compose
  require_docker_daemon
  log "Stopping stack"
  compose down
}

restart_stack() {
  stop_stack
  start_stack
}

show_status() {
  detect_compose
  require_docker_daemon
  compose ps
}

show_logs() {
  detect_compose
  require_docker_daemon
  compose logs -f --tail=200
}

print_help() {
  cat <<'EOF'
Usage: ./bootstrap.sh [command]

Commands:
  up       Build and start the full Docker stack (default)
  down     Stop and remove the Docker stack
  restart  Restart the stack
  status   Show Docker Compose service status
  logs     Follow stack logs
  help     Show this message

Environment:
  STARTUP_TIMEOUT_SECONDS   Override service wait timeout in seconds

Notes:
  - If .env does not exist, it will be created from .env.example.
  - The script prepares runtime directories under SCRATCH_ROOT or ./.runtime.
  - Ollama will automatically pull the configured embedding model before the API starts.
  - Both DeepSeek and Llama vLLM services must become healthy before the API starts.
EOF
}

main() {
  local command="${1:-up}"
  cd "$REPO_ROOT"

  case "$command" in
    up)
      start_stack
      ;;
    down)
      stop_stack
      ;;
    restart)
      restart_stack
      ;;
    status)
      show_status
      ;;
    logs)
      show_logs
      ;;
    help|-h|--help)
      print_help
      ;;
    *)
      fail "Unknown command: $command. Run './bootstrap.sh help' for usage."
      ;;
  esac
}

main "$@"
