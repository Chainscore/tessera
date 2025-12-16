#!/bin/sh
set -e

export PYTHONUNBUFFERED=1

# Log rotation: truncate logs if they exceed 50MB
rotate_logs() {
    for logfile in /app/logs/*.log; do
        if [ -f "$logfile" ]; then
            size=$(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null || echo 0)
            if [ "$size" -gt 52428800 ]; then
                echo "[INFO] Rotating log: $logfile"
                tail -c 10485760 "$logfile" > "$logfile.tmp" && mv "$logfile.tmp" "$logfile"
            fi
        fi
    done
}

# Periodic log rotation in background
(while true; do sleep 300; rotate_logs; done) &

echo "[INFO] Clearing Database..."
rm -rf /app/data/* 2>/dev/null || true

echo "[INFO] Setting up RocksDB library for bundling..."
if [ -f ./setup-rocksdb.sh ]; then
    ./setup-rocksdb.sh || echo "[WARN] setup-rocksdb.sh failed, continuing..."
else
    echo "[INFO] setup-rocksdb.sh not found, skipping..."
fi

# Telemetry host (default: tart-backend:9000 for Docker, localhost:9000 for local)
export TELEMETRY_HOST="${TELEMETRY_HOST:-localhost:9000}"
echo "[INFO] Telemetry host: $TELEMETRY_HOST"

# Create logs directory
mkdir -p /app/logs

start() {
  envfile="$1"
  nodename=$(basename "$envfile" .env)
  # Run without telemetry if TELEMETRY_HOST is empty/unset
  if [ -n "$TELEMETRY_HOST" ]; then
    echo "[entrypoint] starting: uv run jam --env $envfile --telemetry $TELEMETRY_HOST"
    uv run jam --env "$envfile" --telemetry "$TELEMETRY_HOST" 2>&1 | head -c 104857600 > /app/logs/${nodename}.log &
  else
    echo "[entrypoint] starting: uv run jam --env $envfile (no telemetry)"
    uv run jam --env "$envfile" 2>&1 | head -c 104857600 > /app/logs/${nodename}.log &
  fi
}

start envs/40000.env
start envs/40001.env
start envs/40002.env
start envs/40003.env
start envs/40004.env
start envs/40005.env

# Handle signals for graceful shutdown (use signal numbers for sh compatibility)
cleanup() {
    echo "[INFO] Shutting down..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup 15 2

wait

