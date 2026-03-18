#!/usr/bin/env bash
# doom-continuous.sh — Continuous Doom testing agent
# Runs N test cycles, each with shell automation + claude CLI analysis.
# After all cycles, produces an aggregated cross-run report.
# Usage: ./doom-continuous.sh [N]
#   N = number of test cycles (default: 10, minimum: 1)
set -uo pipefail

TESSERA_DIR="$(cd "$(dirname "$0")" && pwd)"
ANALYSIS_DIR="$TESSERA_DIR/test-analysis"
LOG_DIR="$TESSERA_DIR/test-logs"
N="${1:-10}"
COOLDOWN=10  # seconds between cycles

if [ "$N" -lt 1 ]; then
    echo "Error: N must be >= 1"
    exit 1
fi

mkdir -p "$ANALYSIS_DIR"

BATCH_ID="batch-$(date +%Y%m%d-%H%M%S)"
BATCH_DIR="$ANALYSIS_DIR/$BATCH_ID"
mkdir -p "$BATCH_DIR"

BATCH_LOG="$BATCH_DIR/batch.log"

echo "================================================================"
echo "  DOOM CONTINUOUS TESTING AGENT"
echo "  Cycles: $N | Cooldown: ${COOLDOWN}s | Batch: $BATCH_ID"
echo "================================================================"
echo ""

# Track per-cycle results
declare -a LABELS=()
declare -a LOG_FILES=()
declare -a SERVICE_IDS=()
declare -a STATUSES=()  # "ok" or "fail"

{
echo "Batch: $BATCH_ID"
echo "Cycles: $N"
echo "Started: $(date -Iseconds)"
echo ""

for ((i=1; i<=N; i++)); do
    echo "════════════════════════════════════════════════════════════"
    echo "  CYCLE $i / $N"
    echo "════════════════════════════════════════════════════════════"

    # Cooldown between runs
    if [ "$i" -gt 1 ]; then
        echo "[cycle $i] Cooling down ${COOLDOWN}s..."
        sleep "$COOLDOWN"
    fi

    # ── Run testnet lifecycle ────────────────────────────────
    echo "[cycle $i] Starting testnet lifecycle..."
    RUNNER_LOG="/tmp/doom-runner-${BATCH_ID}-${i}.log"
    "$TESSERA_DIR/doom-test-runner.sh" > "$RUNNER_LOG" 2>&1
    RUNNER_EXIT=$?

    RESULT=$(tail -1 "$RUNNER_LOG" 2>/dev/null)

    if [ -z "$RESULT" ] || [ "$RUNNER_EXIT" -ne 0 ]; then
        echo "[cycle $i] FAILED — runner exit=$RUNNER_EXIT"
        LABELS+=("fail-$i")
        LOG_FILES+=("")
        SERVICE_IDS+=("N/A")
        STATUSES+=("runner-fail")
        cp "$RUNNER_LOG" "$BATCH_DIR/cycle-${i}-runner-fail.log" 2>/dev/null
        rm -f "$RUNNER_LOG"
        continue
    fi

    RUN_LABEL=$(echo "$RESULT" | cut -d'|' -f1)
    LOG_FILE=$(echo "$RESULT" | cut -d'|' -f2)
    SERVICE_ID=$(echo "$RESULT" | cut -d'|' -f3)

    LABELS+=("$RUN_LABEL")
    LOG_FILES+=("$LOG_FILE")
    SERVICE_IDS+=("$SERVICE_ID")

    LOG_LINES=$(wc -l < "$LOG_FILE" 2>/dev/null || echo 0)
    echo "[cycle $i] Complete: label=$RUN_LABEL service=$SERVICE_ID ($LOG_LINES lines)"

    # ── Automated grep analysis ──────────────────────────────
    "$TESSERA_DIR/doom-analyze.sh" "$LOG_FILE" "$RUN_LABEL" \
        "$ANALYSIS_DIR/${RUN_LABEL}-builder.log" \
        "$ANALYSIS_DIR/${RUN_LABEL}-monitor.log" \
        "$ANALYSIS_DIR/${RUN_LABEL}-jamt.log" > /dev/null 2>&1

    REPORT="$ANALYSIS_DIR/${RUN_LABEL}-analysis.txt"

    # Check if issues were found
    ISSUE_COUNT=$(grep -c "^  - " "$REPORT" 2>/dev/null || echo 0)
    PANIC_COUNT=$(grep -c "Panic" "$LOG_FILE" 2>/dev/null || echo 0)
    WP_COUNT=$(grep -c "Guaranteed.*Work\|Received.*Work.*Report" "$LOG_FILE" 2>/dev/null || echo 0)
    FRAME_COUNT=$(wc -l < "$ANALYSIS_DIR/${RUN_LABEL}-monitor.log" 2>/dev/null || echo 0)

    if [ "$PANIC_COUNT" -gt 0 ] || [ "$FRAME_COUNT" -eq 0 ]; then
        STATUSES+=("fail")
    else
        STATUSES+=("ok")
    fi

    # ── Claude per-cycle analysis ────────────────────────────
    echo "[cycle $i] Running Claude analysis..."

    # Build focused excerpt
    EXCERPT="/tmp/doom-excerpt-${BATCH_ID}-${i}.txt"
    {
        echo "=== CYCLE $i AUTOMATED REPORT ==="
        sed -n '/SUMMARY/,//p' "$REPORT" 2>/dev/null | head -20
        echo ""
        echo "=== ERRORS ==="
        grep "\[ERROR\]" "$LOG_FILE" | head -20
        echo ""
        echo "=== PANICS ==="
        grep "Panic\|PANIC" "$LOG_FILE" | head -10
        echo ""
        echo "=== HOST CALL COUNTS ==="
        grep -oP 'HOST\(\K\d+' "$LOG_FILE" | sort -n | uniq -c | sort -rn | head -15
        echo ""
        echo "=== INVOKE OUTCOMES (first node only) ==="
        grep "Invoke outcome" "$LOG_FILE" | head -20
        echo ""
        echo "=== PAGE FAULT TYPES ==="
        grep "Page fault at" "$LOG_FILE" | awk -F'/' '{print $NF}' | sort | uniq -c | sort -rn
        echo ""
        echo "=== BUILDER OUTCOME ==="
        tail -10 "$ANALYSIS_DIR/${RUN_LABEL}-builder.log" 2>/dev/null || echo "(empty)"
        echo ""
        echo "=== MONITOR OUTPUT ==="
        cat "$ANALYSIS_DIR/${RUN_LABEL}-monitor.log" 2>/dev/null | head -20 || echo "(empty)"
    } > "$EXCERPT"

    CYCLE_ANALYSIS="$BATCH_DIR/cycle-${i}-analysis.txt"
    claude -p "Analyze this single doom testnet cycle (cycle $i of $N in a continuous run).

Be CONCISE — produce max 30 lines of analysis. Focus on:
1. Did the inner doom PVM panic? If so, at what point (which page fault)?
2. How many page faults were handled before failure?
3. Any new errors not seen in previous analyses?
4. One-line root cause hypothesis.

Known issues from prior investigation:
- U64 type contamination in HOST(12) register passing (refine_fns.py:263)
- Global state mutation in ExecutionStatus enum (status.py)
- Wrong validator assignment in rotation calculation

Log data:
$(<"$EXCERPT")" \
        --print > "$CYCLE_ANALYSIS" 2>/dev/null

    echo ""
    echo "── Cycle $i Analysis ──"
    cat "$CYCLE_ANALYSIS"
    echo ""

    # Symlink analysis into batch dir
    ln -sf "$REPORT" "$BATCH_DIR/cycle-${i}-auto.txt" 2>/dev/null
    rm -f "$RUNNER_LOG" "$EXCERPT"
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ALL $N CYCLES COMPLETE"
echo "════════════════════════════════════════════════════════════"
echo ""

# ── Per-cycle summary table ──────────────────────────────────
echo "┌───────┬──────────┬──────────────┬────────┐"
echo "│ Cycle │ Label    │ Service ID   │ Status │"
echo "├───────┼──────────┼──────────────┼────────┤"
for ((j=0; j<${#LABELS[@]}; j++)); do
    printf "│ %5d │ %-8s │ %-12s │ %-6s │\n" "$((j+1))" "${LABELS[$j]}" "${SERVICE_IDS[$j]}" "${STATUSES[$j]}"
done
echo "└───────┴──────────┴──────────────┴────────┘"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
for s in "${STATUSES[@]}"; do
    if [ "$s" = "ok" ]; then PASS_COUNT=$((PASS_COUNT+1)); else FAIL_COUNT=$((FAIL_COUNT+1)); fi
done
echo "Pass: $PASS_COUNT / $N    Fail: $FAIL_COUNT / $N"
echo ""

} 2>&1 | tee "$BATCH_LOG"

# ── Aggregated Claude analysis ───────────────────────────────
echo ""
echo "[agent] Running aggregated cross-run Claude analysis..."
echo ""

# Collect all per-cycle analyses
AGG_INPUT="/tmp/doom-agg-$$.txt"
{
    echo "=== BATCH SUMMARY ==="
    echo "Cycles: $N, Pass: $PASS_COUNT, Fail: $FAIL_COUNT"
    echo ""
    for ((j=0; j<${#LABELS[@]}; j++)); do
        echo "=== CYCLE $((j+1)): ${LABELS[$j]} (${STATUSES[$j]}) ==="
        CYCLE_A="$BATCH_DIR/cycle-$((j+1))-analysis.txt"
        if [ -f "$CYCLE_A" ]; then
            cat "$CYCLE_A"
        else
            echo "(no analysis)"
        fi
        echo ""
    done

    echo "=== ISSUE FREQUENCY ACROSS ALL RUNS ==="
    for issue_type in INVALID_BLOCKS EPOCH_ERROR NO_REFINE BUILDER_NODE_ERROR NO_WP PYTHON_EXCEPTION MEMORY; do
        COUNT=0
        for label in "${LABELS[@]}"; do
            REPORT="$ANALYSIS_DIR/${label}-analysis.txt"
            if [ -f "$REPORT" ] && grep -q "$issue_type" "$REPORT" 2>/dev/null; then
                COUNT=$((COUNT + 1))
            fi
        done
        if [ "$COUNT" -gt 0 ]; then
            echo "  $issue_type: $COUNT / $N runs"
        fi
    done
} > "$AGG_INPUT"

AGG_REPORT="$BATCH_DIR/aggregated-analysis.txt"

claude -p "You are reviewing $N consecutive doom testnet runs on Tessera.

Produce a structured aggregated report:

1. PATTERN ANALYSIS — What patterns appear across runs? Is the failure consistent or intermittent?
2. FAILURE CLASSIFICATION — Group failures by type. Which are the same root cause?
3. ROOT CAUSES — Ranked by frequency and certainty. Reference specific files and line numbers.
4. SPECIFIC FIXES — Exact code changes needed. Show before/after for each fix.
5. FIX PRIORITY — Which fix to apply first and why.
6. VERIFICATION PLAN — Steps to verify fixes work (what should change in the logs).

Known code locations:
- jam/execution/invocations/functions/refine_fns.py — HOST(12) invoke, HOST(10) poke, HOST(11) pages
- deps/tsrkit-pvm/tsrkit_pvm/common/status.py — ExecutionStatus enum
- jam/utils/assignment.py — validator core assignment
- jam/execution/host_call.py — PsiH outer PVM loop

Data from all runs:
$(<"$AGG_INPUT")" \
    --allowedTools "Read Grep Glob Bash(grep:*) Bash(python3:*)" \
    > "$AGG_REPORT" 2>/dev/null

echo "================================================================"
echo "  AGGREGATED ANALYSIS ($N RUNS)"
echo "================================================================"
echo ""
cat "$AGG_REPORT"
echo ""
echo "================================================================"
echo "  Batch directory: $BATCH_DIR/"
echo "  Aggregated report: $AGG_REPORT"
echo "  Per-cycle analyses: $BATCH_DIR/cycle-*-analysis.txt"
echo "================================================================"

# Cleanup
rm -f "$AGG_INPUT"

echo ""
echo "To apply fixes, run:"
echo "  claude -p 'Read $AGG_REPORT and apply ALL SPECIFIC FIXES' --allowedTools 'Read Edit Grep Glob'"
