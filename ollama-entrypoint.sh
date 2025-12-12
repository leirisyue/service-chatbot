#!/usr/bin/env bash
set -euo pipefail

# Start ollama serve in background
ollama serve &

# Wait for Ollama TCP port to be ready (no curl needed)
echo "[entrypoint] Waiting for Ollama TCP port 11434..."
for i in {1..60}; do
  if bash -c 'exec 3<>/dev/tcp/localhost/11434' 2>/dev/null; then
    echo "[entrypoint] Ollama TCP port is open."
    break
  fi
  sleep 1
done

# Pull embedding model (from env; default qwen3-embedding:latest)
EMBED_MODEL="${APP_EMBEDDING_MODEL:-qwen3-embedding:latest}"
echo "[entrypoint] Pulling embedding model: ${EMBED_MODEL}"
# Retry a few times in case of network hiccups
for i in {1..3}; do
  if ollama pull "${EMBED_MODEL}"; then
    echo "[entrypoint] Pulled ${EMBED_MODEL} successfully."
    break
  fi
  echo "[entrypoint] Retry ${i} pulling ${EMBED_MODEL}..."
  sleep 3
done || true

# Keep container alive
echo "[entrypoint] Ollama service started. Sleeping indefinitely."
sleep infinity