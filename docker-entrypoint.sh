#!/bin/sh
set -eu

cd /app

VENV_BIN="/app/.venv/bin"
export PYTHONUNBUFFERED=1

enabled() {
    case "${1:-}" in
        1|true|TRUE|True|yes|YES|Yes|on|ON|On)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

setup_rocksdb() {
    if [ -f ./setup-rocksdb.sh ]; then
        ./setup-rocksdb.sh || echo "[WARN] setup-rocksdb.sh failed, continuing..."
    fi
}

start_node() {
    envfile="$1"
    nodeid=$(basename "$envfile" .env)
    nodename=$(sed -n 's/^NODE_NAME=//p' "$envfile" 2>/dev/null | head -n 1)
    nodename="${nodename:-$nodeid}"
    logfile="/app/logs/${nodeid}.log"

    mkdir -p /app/logs
    : >"$logfile"

    if [ -n "${TELEMETRY_HOST:-}" ]; then
        echo "[entrypoint] starting node ${nodename} (${nodeid}): jam --env ${envfile} --telemetry ${TELEMETRY_HOST}"
        "$VENV_BIN/jam" --env "$envfile" --telemetry "$TELEMETRY_HOST" 2>&1 \
            | while IFS= read -r line; do
                printf '%s\n' "$line" >>"$logfile"
                printf '[%s] %s\n' "$nodename" "$line"
            done &
    else
        echo "[entrypoint] starting node ${nodename} (${nodeid}): jam --env ${envfile}"
        "$VENV_BIN/jam" --env "$envfile" 2>&1 \
            | while IFS= read -r line; do
                printf '%s\n' "$line" >>"$logfile"
                printf '[%s] %s\n' "$nodename" "$line"
            done &
    fi
}

start_nodes() {
    echo "[INFO] Clearing node database..."
    rm -rf /app/data/* 2>/dev/null || true

    echo "[INFO] Setting up RocksDB library for node mode..."
    setup_rocksdb

    export TELEMETRY_HOST="${TELEMETRY_HOST:-localhost:9000}"
    if [ "$#" -eq 1 ]; then
        echo "[INFO] Starting single-node mode"
    else
        echo "[INFO] Starting testnet mode with $# nodes"
    fi

    for envfile in "$@"; do
        start_node "$envfile"
    done

    cleanup() {
        echo "[INFO] Shutting down..."
        kill $(jobs -p) 2>/dev/null || true
        exit 0
    }

    trap cleanup 15 2
    wait
}

single_node_env() {
    if [ -n "${TESSERA_ENV:-}" ]; then
        echo "$TESSERA_ENV"
        return
    fi

    if [ -n "${TESSERA_NODE:-}" ]; then
        case "$TESSERA_NODE" in
            *.env)
                echo "$TESSERA_NODE"
                ;;
            envs/*)
                echo "$TESSERA_NODE"
                ;;
            *)
                echo "envs/${TESSERA_NODE}.env"
                ;;
        esac
        return
    fi

    echo "envs/40000.env"
}

start_fuzzer() {
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
    export JAM_LOG_DIR="$JAM_FUZZ_DATA_PATH/logs"
    export JAM_STATE_TRIE_CACHE_LIMIT="${JAM_STATE_TRIE_CACHE_LIMIT:-2}"
    export JAM_PRUNE_BLOCK_HISTORY="${JAM_PRUNE_BLOCK_HISTORY:-0}"

    if [ -n "${JAM_FUZZ_LOG_LEVEL:-}" ]; then
        export JAM_LOG_LEVEL="$JAM_FUZZ_LOG_LEVEL"
    else
        export JAM_LOG_LEVEL="${JAM_LOG_LEVEL:-info}"
    fi

    echo "[INFO] Starting fuzzer target mode"
    echo "[INFO] spec=${JAM_FUZZ_SPEC} db=${JAM_FUZZ_DATA_PATH} socket=${JAM_FUZZ_SOCK_PATH}"
    echo "[INFO] block_history_pruning=${JAM_PRUNE_BLOCK_HISTORY}"

    exec "$VENV_BIN/python" jam/cli.py \
        --fuzzer \
        --db "$JAM_FUZZ_DATA_PATH" \
        --socket "$JAM_FUZZ_SOCK_PATH" \
        --no-record
}

node_mode_wip() {
    mode="$1"
    echo "[INFO] ${mode} is currently work in progress for this Docker image."
    echo "[INFO] Fuzzer target mode is enabled. Start with JAM_FUZZ=1 or FUZZ_MODE=on."
    exit 0
}

FUZZ_SWITCH="${JAM_FUZZ:-${FUZZ_MODE:-}}"

if enabled "$FUZZ_SWITCH"; then
    start_fuzzer
elif enabled "${TESTNET:-}"; then
    node_mode_wip "Testnet mode"
else
    node_mode_wip "Single-node mode"
fi
