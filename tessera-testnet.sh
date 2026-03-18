#!/usr/bin/env bash
set -uo pipefail

NODES=(0 1 2 3 4 5)
PIDS=()
SIGINT_COUNT=0

# ── Signal handler ──────────────────────────────────────────
# First  Ctrl+C → nodes show warning (SIGINT goes to process group automatically)
# Second Ctrl+C → nodes begin graceful shutdown
# Third  Ctrl+C → force kill everything
handle_signal() {
  SIGINT_COUNT=$((SIGINT_COUNT + 1))

  if [ "$SIGINT_COUNT" -eq 1 ]; then
    echo ""
    echo -e "\033[1;91m ⚠  Press Ctrl+C again to shut down testnet.\033[0m"

  elif [ "$SIGINT_COUNT" -eq 2 ]; then
    echo ""
    echo -e "\033[1;93m ⏳ Shutting down testnet... waiting for nodes to exit.\033[0m"
    # Nodes already received second SIGINT from process group → graceful shutdown started.
    # Give them time, then check for stragglers.
    (
      sleep 5
      for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
          echo -e "\033[1;91m 💀 Force killing node (pid $pid)\033[0m"
          kill -9 "$pid" 2>/dev/null || true
        fi
      done
    ) &

  else
    echo ""
    echo -e "\033[1;91m 💀 Force killing all nodes.\033[0m"
    for pid in "${PIDS[@]}"; do
      kill -9 "$pid" 2>/dev/null || true
    done
    pkill -9 -f "uv run jam/cli.py" 2>/dev/null || true
    exit 1
  fi
}

trap handle_signal SIGINT SIGTERM

# ── Load base .env ──────────────────────────────────────────
BASE_ENV=()
if [ -f ".env" ]; then
  while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    BASE_ENV+=("$key=$value")
  done < ".env"
fi

LOG_LEVEL="${JAM_LOG_LEVEL:-trace}"
PVM_MODE="${PVM_MODE:-recompiler}"

# ── Start nodes ─────────────────────────────────────────────
echo "🚀 Starting Tessera testnet..."

for i in "${NODES[@]}"; do
  ENV_FILE="envs/4000${i}.env"

  # Per-node env overrides base .env
  NODE_ENV=()
  if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
      [[ -z "$key" || "$key" == \#* ]] && continue
      NODE_ENV+=("$key=$value")
    done < "$ENV_FILE"
  fi

  echo "▶️  Starting node $i (JAM_LOG_LEVEL=$LOG_LEVEL)"

  env PVM_MODE="$PVM_MODE" "${BASE_ENV[@]}" "${NODE_ENV[@]}" \
    uv run jam/cli.py --env "$ENV_FILE" \
    > >(sed -u "s/^/[node$i] /") 2>&1 &

  PIDS+=($!)
done

echo "✅ Tessera testnet running (Ctrl+C twice to stop)"

# ── Wait loop ───────────────────────────────────────────────
# `wait` returns when interrupted by a signal. Re-wait until
# all children have actually exited or we've force-killed them.
while true; do
  # Check if any node is still alive
  alive=0
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      alive=1
      break
    fi
  done

  if [ "$alive" -eq 0 ]; then
    break
  fi

  wait 2>/dev/null || true
done

if [ "$SIGINT_COUNT" -gt 0 ]; then
  echo -e "\033[1;92m ✔  All nodes stopped.\033[0m"
else
  echo -e "\033[1;91m ✘  Nodes exited unexpectedly.\033[0m"
  exit 1
fi
