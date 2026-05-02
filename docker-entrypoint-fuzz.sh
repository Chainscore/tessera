#!/bin/sh
set -eu

cd /app

if [ -z "${JAM_FUZZ:-}" ]; then
    export TELEMETRY_HOST="${TELEMETRY_HOST:-localhost:9000}"
    mkdir -p /app/logs

    start() {
      envfile="$1"
      nodename=$(basename "$envfile" .env)
      if [ -n "$TELEMETRY_HOST" ]; then
          uv run jam --env "$envfile" --telemetry "$TELEMETRY_HOST" > "/app/logs/${nodename}.log" 2>&1 &
      else
          uv run jam --env "$envfile" > "/app/logs/${nodename}.log" 2>&1 &
      fi
    }

    start envs/40000.env

    cleanup() {
        kill $(jobs -p) 2>/dev/null || true
        exit 0
    }

    trap cleanup 15 2
    wait
fi

: "${JAM_FUZZ_SPEC:?JAM_FUZZ_SPEC is required}"
: "${JAM_FUZZ_DATA_PATH:?JAM_FUZZ_DATA_PATH is required}"
: "${JAM_FUZZ_SOCK_PATH:?JAM_FUZZ_SOCK_PATH is required}"

case "$JAM_FUZZ_SPEC" in
    tiny|full)
        ;;
    *)
        echo "Unsupported JAM_FUZZ_SPEC: $JAM_FUZZ_SPEC" >&2
        exit 1
        ;;
esac

mkdir -p "$JAM_FUZZ_DATA_PATH"
mkdir -p "$(dirname "$JAM_FUZZ_SOCK_PATH")"

export JAM_CHAIN_SPEC="$JAM_FUZZ_SPEC"

if [ -n "${JAM_FUZZ_LOG_LEVEL:-}" ]; then
    export JAM_LOG_LEVEL="$JAM_FUZZ_LOG_LEVEL"
fi

exec uv run python jam/cli.py \
    --fuzzer \
    --db "$JAM_FUZZ_DATA_PATH" \
    --socket "$JAM_FUZZ_SOCK_PATH" \
    --no-record
