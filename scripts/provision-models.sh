#!/bin/sh
# Ensures the models required by Sovereign AI Workbench exist in Ollama.
# Idempotent: models already present are never pulled again, so restarts
# with a warm ollama-models volume finish instantly.
# Required env:
#   OLLAMA_HOST      - Ollama endpoint, e.g. http://ollama:11434
#   REQUIRED_MODELS  - space-separated pull tags, e.g. "qwen2.5:3b-instruct moondream:latest nomic-embed-text:latest"
set -eu

: "${OLLAMA_HOST:?OLLAMA_HOST must be set}"
: "${REQUIRED_MODELS:?REQUIRED_MODELS must be set}"

MAX_WAIT_SECS="${OLLAMA_WAIT_SECS:-300}"
POLL_SECS="${OLLAMA_POLL_SECS:-5}"

echo "[Builder AI] Waiting for Ollama at ${OLLAMA_HOST}..."
elapsed=0
until ollama list >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$MAX_WAIT_SECS" ]; then
    echo "[Builder AI] ERROR: Ollama not reachable after ${MAX_WAIT_SECS}s. Aborting." >&2
    exit 1
  fi
  sleep "$POLL_SECS"
  elapsed=$((elapsed + POLL_SECS))
done

echo "[Builder AI] Checking required models..."
failed=0
# shellcheck disable=SC2086
for model in $REQUIRED_MODELS; do
  if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx "$model"; then
    echo "[Builder AI] ${model}: available"
  else
    # 'name' and 'name:latest' are the same model; accept a bare-name hit too.
    base="${model%:*}"
    if [ "$base" != "$model" ] && ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx "$base"; then
      echo "[Builder AI] ${model}: available (as ${base})"
    else
      echo "[Builder AI] ${model}: missing -> pulling (this can take several minutes per model)..."
      if ollama pull "$model"; then
        echo "[Builder AI] ${model}: pulled"
      else
        echo "[Builder AI] ERROR: failed to pull ${model}." >&2
        failed=1
      fi
    fi
  fi
done

if [ "$failed" -ne 0 ]; then
  echo "[Builder AI] ERROR: one or more required models are missing. Check the log above." >&2
  exit 1
fi

echo "[Builder AI] Required models ready."
