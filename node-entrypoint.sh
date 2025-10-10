#!/bin/sh
set -e

export PYTHONUNBUFFERED=1

echo "[INFO] Clearing Database..."
rm -rf /app/data/*

# Accept one arg
envfile="${1:-}"

if [ -z "$envfile" ]; then
  echo "[entrypoint] ERROR: no env file specified (usage: /entrypoint.sh envs/40000.env)" >&2
  exit 2
fi

echo "[entrypoint] starting: uv run jam --env $envfile" >&2
exec /root/.local/bin/uv run jam --env "$envfile"
