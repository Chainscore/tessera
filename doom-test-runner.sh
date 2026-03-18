#!/usr/bin/env bash
# doom-test-runner.sh — Core workflow for running PolkaDoom on Tessera testnet
# Usage: ./doom-test-runner.sh [run_label]
# Returns the log file path and run label via stdout (last line)
set -uo pipefail

TESSERA_DIR="$(cd "$(dirname "$0")" && pwd)"
PJ_DIR="$HOME/Downloads/Teams/polkajam"
LOG_DIR="$TESSERA_DIR/test-logs"
ANALYSIS_DIR="$TESSERA_DIR/test-analysis"
RUN_LABEL="${1:-}"
SESSION="tessera"
NAMES=(alice bob charlie dave eve fergie)
NODES=(0 1 2 3 4 5)

# Timeouts
TESTNET_SETTLE_SECS=15
JAMT_TIMEOUT=300       # 5 min for service creation
BUILDER_TIMEOUT=300    # 5 min for builder
MONITOR_TIMEOUT=300    # 5 min monitor
POST_BUILD_WAIT=60     # Wait after builder starts for WP processing

# Temp files for capturing tool output
JAMT_LOG="/tmp/doom-jamt-$$.log"
BUILDER_LOG="/tmp/doom-builder-$$.log"
MONITOR_LOG="/tmp/doom-monitor-$$.log"
RUN_META="/tmp/doom-run-meta-$$.json"

cleanup() {
    # Kill background processes
    [ -n "${BUILDER_PID:-}" ] && kill "$BUILDER_PID" 2>/dev/null || true
    [ -n "${MONITOR_PID:-}" ] && kill "$MONITOR_PID" 2>/dev/null || true
    # Don't remove temp logs — analysis needs them
}
trap cleanup EXIT

log() { echo "[doom-runner] $(date +%H:%M:%S) $*" >&2; }
die() { log "FATAL: $*"; exit 1; }

# ── Phase 1: Check prerequisites ────────────────────────────
log "Phase 1: Checking prerequisites..."
[ -f "$TESSERA_DIR/tessera-tmux.sh" ] || die "tessera-tmux.sh not found"
[ -x "$PJ_DIR/jamt" ] || die "jamt not found or not executable at $PJ_DIR/jamt"
[ -x "$PJ_DIR/corevm-builder" ] || die "corevm-builder not found"
[ -x "$PJ_DIR/corevm-monitor" ] || die "corevm-monitor not found"
[ -f "$PJ_DIR/doom.corevm" ] || die "doom.corevm not found"

# Kill any existing tessera session
tmux kill-session -t "$SESSION" 2>/dev/null || true
sleep 1

# ── Phase 2: Start Tessera testnet ──────────────────────────
log "Phase 2: Starting Tessera testnet..."

# We start the tmux session directly (not via the interactive script)
# because we need non-interactive control
cd "$TESSERA_DIR"

# Source and create the tmux session from tessera-tmux.sh logic
# but without the interactive attach loop
BASE_ENV_ARGS=()
if [ -f ".env" ]; then
    while IFS='=' read -r key value; do
        [[ -z "$key" || "$key" == \#* ]] && continue
        BASE_ENV_ARGS+=("$key=$value")
    done < ".env"
fi

LOG_LEVEL="${JAM_LOG_LEVEL:-trace}"
PVM_MODE="${PVM_MODE:-recompiler}"

TMP_LOGS=()
for i in "${NODES[@]}"; do
    TMP_LOGS+=("/tmp/tessera-node${i}.log")
    : > "/tmp/tessera-node${i}.log"  # Clear old logs
done

# Write per-node launcher scripts
for idx in "${NODES[@]}"; do
    SCRIPT="/tmp/tessera-run-node${idx}.sh"
    ENV_FILE="envs/4000${idx}.env"
    {
        echo '#!/usr/bin/env bash'
        echo "cd $(printf '%q' "$PWD")"
        echo "export PVM_MODE=$(printf '%q' "$PVM_MODE")"
        # Enable vector recording on alice (node 0) only
        if [ "$idx" = "0" ]; then
            echo "export JAM_VECTOR_RECORD=${RUN_LABEL:-doom}"
        fi
        for v in "${BASE_ENV_ARGS[@]}"; do
            echo "export $v"
        done
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

# Create tmux session
tmux kill-session -t "$SESSION" 2>/dev/null || true
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
tmux select-layout -t "$SESSION" tiled

log "Testnet launched. Waiting ${TESTNET_SETTLE_SECS}s for nodes to connect..."
sleep "$TESTNET_SETTLE_SECS"

# Quick health check: see if any node log has content
NODE_ALIVE=false
for i in "${NODES[@]}"; do
    if [ -s "${TMP_LOGS[$i]}" ]; then
        NODE_ALIVE=true
        break
    fi
done
$NODE_ALIVE || die "No node produced any log output after ${TESTNET_SETTLE_SECS}s"
log "Nodes are alive."

# ── Phase 3: Create CoreVM service via jamt ──────────────────
log "Phase 3: Creating CoreVM service (doom)..."
cd "$PJ_DIR"

timeout "$JAMT_TIMEOUT" ./jamt vm new ./doom.corevm 10000000 > "$JAMT_LOG" 2>&1 &
JAMT_PID=$!

# Wait for jamt to complete
wait "$JAMT_PID" 2>/dev/null
JAMT_EXIT=$?

if [ "$JAMT_EXIT" -ne 0 ]; then
    log "WARNING: jamt exited with code $JAMT_EXIT"
    cat "$JAMT_LOG" >&2
fi

# Extract service ID from jamt output
SERVICE_ID=""
if [ -f "$JAMT_LOG" ]; then
    # Look for "Service id: HEXID" or "Service HEXID created"
    SERVICE_ID=$(grep -oP 'Service id:\s*\K[0-9a-fA-F]+' "$JAMT_LOG" | head -1)
    if [ -z "$SERVICE_ID" ]; then
        SERVICE_ID=$(grep -oP 'Service\s+\K[0-9a-fA-F]+(?=\s+created)' "$JAMT_LOG" | head -1)
    fi
fi

if [ -z "$SERVICE_ID" ]; then
    log "ERROR: Could not extract service ID from jamt output"
    log "jamt output:"
    cat "$JAMT_LOG" >&2
    # Still continue — we'll record the failure
    SERVICE_ID="UNKNOWN"
fi

log "Service ID: $SERVICE_ID"

# ── Phase 4: Start corevm-builder and corevm-monitor ────────
if [ "$SERVICE_ID" != "UNKNOWN" ]; then
    log "Phase 4: Starting corevm-builder and corevm-monitor..."
    cd "$PJ_DIR"

    # Start monitor in background
    RUST_LOG=corevm timeout "$MONITOR_TIMEOUT" ./corevm-monitor "$SERVICE_ID" > "$MONITOR_LOG" 2>&1 &
    MONITOR_PID=$!
    log "Monitor started (PID $MONITOR_PID)"

    # Start builder (this submits WPs and runs doom refinement)
    RUST_LOG=corevm timeout "$BUILDER_TIMEOUT" ./corevm-builder "$SERVICE_ID" --refine-gas 1000000000 > "$BUILDER_LOG" 2>&1 &
    BUILDER_PID=$!
    log "Builder started (PID $BUILDER_PID)"

    # Wait for builder to finish or timeout
    wait "$BUILDER_PID" 2>/dev/null
    BUILDER_EXIT=$?
    log "Builder finished (exit=$BUILDER_EXIT)"

    # Give monitor a few more seconds to catch up, then kill it
    sleep 5
    kill "$MONITOR_PID" 2>/dev/null || true
    wait "$MONITOR_PID" 2>/dev/null
    MONITOR_EXIT=$?
    log "Monitor stopped (exit=$MONITOR_EXIT)"
else
    log "Skipping builder/monitor due to missing service ID"
    BUILDER_EXIT=1
    MONITOR_EXIT=1
    : > "$BUILDER_LOG"
    : > "$MONITOR_LOG"
fi

# ── Phase 5: Stop testnet and save logs ──────────────────────
log "Phase 5: Stopping testnet..."
cd "$TESSERA_DIR"

# Send Ctrl+C to all panes
for p in 0 1 2 3 4 5; do
    tmux send-keys -t "$SESSION:.$p" C-c 2>/dev/null || true
done
sleep 3

# Send second Ctrl+C for graceful shutdown
for p in 0 1 2 3 4 5; do
    tmux send-keys -t "$SESSION:.$p" C-c 2>/dev/null || true
done
sleep 3

# Find next log number
mkdir -p "$LOG_DIR"
max=-1
for f in "$LOG_DIR"/l*.txt; do
    [ -e "$f" ] || continue
    base="$(basename "$f" .txt)"
    num="${base#l}"
    if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -gt "$max" ]; then
        max=$num
    fi
done
NEXT=$((max + 1))
LOG_FILE="$LOG_DIR/l${NEXT}.txt"

# Consolidate node logs
: > "$LOG_FILE"
for i in "${NODES[@]}"; do
    if [ -f "${TMP_LOGS[$i]}" ]; then
        printf '════════════════════ %s :4000%s ════════════════════\n' "${NAMES[$i]}" "$i" >> "$LOG_FILE"
        cat "${TMP_LOGS[$i]}" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
    fi
done

# Kill tmux session
tmux kill-session -t "$SESSION" 2>/dev/null || true
log "Testnet stopped. Node logs saved to $LOG_FILE"

# ── Phase 6: Save run metadata ───────────────────────────────
mkdir -p "$ANALYSIS_DIR"

if [ -z "$RUN_LABEL" ]; then
    RUN_LABEL="l${NEXT}"
fi

cat > "$RUN_META" <<EOF
{
    "run_label": "$RUN_LABEL",
    "log_number": $NEXT,
    "log_file": "$LOG_FILE",
    "service_id": "$SERVICE_ID",
    "jamt_exit": $JAMT_EXIT,
    "builder_exit": ${BUILDER_EXIT:-1},
    "monitor_exit": ${MONITOR_EXIT:-1},
    "timestamp": "$(date -Iseconds)",
    "jamt_log": "$JAMT_LOG",
    "builder_log": "$BUILDER_LOG",
    "monitor_log": "$MONITOR_LOG"
}
EOF

# Copy tool logs to analysis dir
cp "$JAMT_LOG" "$ANALYSIS_DIR/${RUN_LABEL}-jamt.log" 2>/dev/null || true
cp "$BUILDER_LOG" "$ANALYSIS_DIR/${RUN_LABEL}-builder.log" 2>/dev/null || true
cp "$MONITOR_LOG" "$ANALYSIS_DIR/${RUN_LABEL}-monitor.log" 2>/dev/null || true
cp "$RUN_META" "$ANALYSIS_DIR/${RUN_LABEL}-meta.json" 2>/dev/null || true

log "Run complete. Label: $RUN_LABEL"
log "Analysis artifacts in $ANALYSIS_DIR/${RUN_LABEL}-*"

# Output the run label and log path (for calling scripts to parse)
echo "$RUN_LABEL|$LOG_FILE|$SERVICE_ID|$NEXT"
