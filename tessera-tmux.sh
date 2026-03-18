#!/usr/bin/env bash
set -uo pipefail

SESSION="tessera"
NODES=(0 1 2 3 4 5)
NAMES=(alice bob charlie dave eve fergie)
LOG_DIR="test-logs"
TMP_LOGS=()

for i in "${NODES[@]}"; do
  TMP_LOGS+=("/tmp/tessera-node${i}.log")
done

# ── Load base .env ──────────────────────────────────────────
BASE_ENV_ARGS=()
if [ -f ".env" ]; then
  while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    BASE_ENV_ARGS+=("$key=$value")
  done < ".env"
fi

LOG_LEVEL="${JAM_LOG_LEVEL:-trace}"
PVM_MODE="${PVM_MODE:-recompiler}"

# ── Write per-node launcher scripts ─────────────────────────
for idx in "${NODES[@]}"; do
  SCRIPT="/tmp/tessera-run-node${idx}.sh"
  ENV_FILE="envs/4000${idx}.env"

  {
    echo '#!/usr/bin/env bash'
    echo "cd $(printf '%q' "$PWD")"
    echo "export PVM_MODE=$(printf '%q' "$PVM_MODE")"

    # Base env vars
    for v in "${BASE_ENV_ARGS[@]}"; do
      echo "export $v"
    done

    # Per-node env overrides
    if [ -f "$ENV_FILE" ]; then
      while IFS='=' read -r key value; do
        [[ -z "$key" || "$key" == \#* ]] && continue
        echo "export ${key}=${value}"
      done < "$ENV_FILE"
    fi

    echo "exec uv run jam/cli.py --env $(printf '%q' "$ENV_FILE") 2>&1 | tee >(sed 's/\x1b\[[0-9;]*m//g' > ${TMP_LOGS[$idx]})"
  } > "$SCRIPT"
  chmod +x "$SCRIPT"
done

# ── Kill existing session ───────────────────────────────────
tmux kill-session -t "$SESSION" 2>/dev/null || true

# ── Prepare logs dir ────────────────────────────────────────
mkdir -p "$LOG_DIR"

# ── Write shutdown helper script ────────────────────────────
# This runs OUTSIDE tmux when triggered by the detach hook
SHUTDOWN_SCRIPT="/tmp/tessera-shutdown.sh"
cat > "$SHUTDOWN_SCRIPT" <<'SHUTDOWN_EOF'
#!/usr/bin/env bash
SESSION="tessera"
LOG_DIR="$1"
shift
NAMES=("$@")
NODES=(0 1 2 3 4 5)
TMP_LOGS=()
for i in "${NODES[@]}"; do
  TMP_LOGS+=("/tmp/tessera-node${i}.log")
done

# Find next available lN.txt number
max=-1
for f in "$LOG_DIR"/l*.txt; do
  [ -e "$f" ] || continue
  base="$(basename "$f" .txt)"
  num="${base#l}"
  if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -gt "$max" ]; then
    max=$num
  fi
done

next=$((max + 1))
dest="$LOG_DIR/l${next}.txt"
: > "$dest"
for i in "${NODES[@]}"; do
  if [ -f "${TMP_LOGS[$i]}" ]; then
    printf '════════════════════ %s :4000%s ════════════════════\n' "${NAMES[$i]}" "$i" >> "$dest"
    cat "${TMP_LOGS[$i]}" >> "$dest"
    echo "" >> "$dest"
  fi
done
echo "$dest"
SHUTDOWN_EOF
chmod +x "$SHUTDOWN_SCRIPT"

# ── Create tmux session with 6 panes (2x3 grid) ────────────
tmux new-session -d -s "$SESSION" -x 240 -y 60
tmux send-keys -t "$SESSION" "/tmp/tessera-run-node0.sh" Enter

tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" "/tmp/tessera-run-node1.sh" Enter

tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" "/tmp/tessera-run-node2.sh" Enter

tmux select-layout -t "$SESSION" tiled

tmux select-pane -t "$SESSION:.0"
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" "/tmp/tessera-run-node3.sh" Enter

tmux select-pane -t "$SESSION:.2"
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" "/tmp/tessera-run-node4.sh" Enter

tmux select-pane -t "$SESSION:.4"
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" "/tmp/tessera-run-node5.sh" Enter

# ── Apply 2x3 tiled layout and configure pane titles ───────
tmux select-layout -t "$SESSION" tiled

tmux set-option -t "$SESSION" pane-border-status top
tmux set-option -t "$SESSION" pane-border-format " #{pane_index}: #T "

PANE_NAMES=("alice :40000" "dave :40003" "bob :40001" "eve :40004" "charlie :40002" "fergie :40005")
for p in 0 1 2 3 4 5; do
  tmux select-pane -t "$SESSION:.$p" -T "${PANE_NAMES[$p]}"
done

tmux select-pane -t "$SESSION:.0"

# ── Attach to tmux (foreground) ─────────────────────────────
# Ctrl+C inside tmux goes to the running node process in the active pane.
# To shut down: press Ctrl+B then Q (our custom binding below), or just
# use the wrapper loop below.
echo -e "\033[1;92m Tessera testnet launched in tmux session '$SESSION'\033[0m"
echo -e "\033[1;92m Ctrl+C twice to stop and save logs.\033[0m"
echo ""

# ── Main loop: attach, handle Ctrl+C on detach/exit ─────────
SIGINT_COUNT=0

trap '' SIGINT  # Ignore SIGINT while we set up

(
  # This subshell manages the lifecycle
  trap 'true' SIGINT

  while true; do
    # Re-enable SIGINT for the attach call so Ctrl+C detaches us
    trap - SIGINT
    tmux attach-session -t "$SESSION" 2>/dev/null
    ATTACH_EXIT=$?
    trap 'true' SIGINT

    # Check if session still exists
    if ! tmux has-session -t "$SESSION" 2>/dev/null; then
      echo -e "\033[1;93m Tmux session ended.\033[0m"
      DEST=$("$SHUTDOWN_SCRIPT" "$LOG_DIR" "${NAMES[@]}")
      echo -e "\033[1;94m Logs saved to $DEST\033[0m"
      break
    fi

    # We got detached (likely by Ctrl+C)
    SIGINT_COUNT=$((SIGINT_COUNT + 1))

    if [ "$SIGINT_COUNT" -eq 1 ]; then
      echo ""
      echo -e "\033[1;91m Press Ctrl+C again to shut down testnet.\033[0m"
      echo -e "\033[1;90m Re-attaching in 5s...\033[0m"
      # Send Ctrl+C to all panes (first warning)
      for p in 0 1 2 3 4 5; do
        tmux send-keys -t "$SESSION:.$p" C-c 2>/dev/null || true
      done
      sleep 5
      # Re-attach so user can see what happened
      continue

    elif [ "$SIGINT_COUNT" -eq 2 ]; then
      echo ""
      echo -e "\033[1;93m Shutting down testnet... waiting for nodes.\033[0m"
      for p in 0 1 2 3 4 5; do
        tmux send-keys -t "$SESSION:.$p" C-c 2>/dev/null || true
      done
      sleep 3
      DEST=$("$SHUTDOWN_SCRIPT" "$LOG_DIR" "${NAMES[@]}")
      tmux kill-session -t "$SESSION" 2>/dev/null || true
      echo -e "\033[1;92m All nodes stopped.\033[0m"
      echo -e "\033[1;94m Logs saved to $DEST\033[0m"
      break

    else
      echo ""
      echo -e "\033[1;91m Force killing all nodes.\033[0m"
      DEST=$("$SHUTDOWN_SCRIPT" "$LOG_DIR" "${NAMES[@]}")
      tmux kill-session -t "$SESSION" 2>/dev/null || true
      pkill -9 -f "uv run jam/cli.py" 2>/dev/null || true
      echo -e "\033[1;94m Logs saved to $DEST\033[0m"
      break
    fi
  done
)
