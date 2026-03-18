#!/usr/bin/env bash
# doom-single.sh — Single on-demand Doom test agent
# Uses shell for testnet lifecycle + claude CLI for intelligent analysis
# Usage: ./doom-single.sh
set -uo pipefail

TESSERA_DIR="$(cd "$(dirname "$0")" && pwd)"
ANALYSIS_DIR="$TESSERA_DIR/test-analysis"
LOG_DIR="$TESSERA_DIR/test-logs"

mkdir -p "$ANALYSIS_DIR"

echo "================================================================"
echo "  DOOM SINGLE TEST AGENT — On-Demand Deep Analysis"
echo "================================================================"
echo ""

# ── Phase 1: Run the testnet lifecycle ───────────────────────
echo "[agent] Phase 1: Running testnet lifecycle..."
echo "[agent] Starting 6 tessera nodes + jamt + corevm-builder + monitor"
echo ""

RUNNER_LOG="/tmp/doom-runner-$$.log"
"$TESSERA_DIR/doom-test-runner.sh" > "$RUNNER_LOG" 2>&1
RUNNER_EXIT=$?

RESULT=$(tail -1 "$RUNNER_LOG")
RUNNER_STDERR=$(head -n -1 "$RUNNER_LOG")

# Show runner progress to user
echo "$RUNNER_STDERR"
echo ""

if [ -z "$RESULT" ] || [ "$RUNNER_EXIT" -ne 0 ]; then
    echo "[agent] ERROR: Test runner failed (exit=$RUNNER_EXIT)"
    echo "[agent] Runner output saved to $RUNNER_LOG"
    echo ""
    echo "[agent] Invoking claude to diagnose runner failure..."
    claude -p "The doom-test-runner.sh script failed with exit code $RUNNER_EXIT. Here is its output:

$(cat "$RUNNER_LOG")

Diagnose why the runner failed. The runner starts a 6-node tessera testnet via tmux, then runs jamt to create a CoreVM service, then corevm-builder and corevm-monitor. What went wrong and how to fix it?" --allowedTools "Bash(ls:*) Bash(cat:*) Read"
    exit 1
fi

RUN_LABEL=$(echo "$RESULT" | cut -d'|' -f1)
LOG_FILE=$(echo "$RESULT" | cut -d'|' -f2)
SERVICE_ID=$(echo "$RESULT" | cut -d'|' -f3)
LOG_NUM=$(echo "$RESULT" | cut -d'|' -f4)

echo "[agent] Run complete: label=$RUN_LABEL service=$SERVICE_ID"
echo "[agent] Node logs: $LOG_FILE ($(wc -l < "$LOG_FILE") lines)"
echo ""

# ── Phase 2: Quick automated grep analysis ───────────────────
echo "[agent] Phase 2: Running automated log scan..."
"$TESSERA_DIR/doom-analyze.sh" "$LOG_FILE" "$RUN_LABEL" \
    "$ANALYSIS_DIR/${RUN_LABEL}-builder.log" \
    "$ANALYSIS_DIR/${RUN_LABEL}-monitor.log" \
    "$ANALYSIS_DIR/${RUN_LABEL}-jamt.log" > /dev/null 2>&1

REPORT="$ANALYSIS_DIR/${RUN_LABEL}-analysis.txt"
echo "[agent] Automated scan saved: $REPORT"
echo ""

# ── Phase 3: Claude deep analysis ────────────────────────────
echo "[agent] Phase 3: Invoking Claude for deep analysis..."
echo "[agent] This reads node logs, builder/monitor output, and prior findings."
echo ""

# Build a focused log excerpt for claude (full logs can be 50k+ lines)
EXCERPT="/tmp/doom-excerpt-$$.txt"
{
    echo "=== AUTOMATED ANALYSIS REPORT ==="
    cat "$REPORT"
    echo ""
    echo "=== BUILDER LOG (last 200 lines) ==="
    tail -200 "$ANALYSIS_DIR/${RUN_LABEL}-builder.log" 2>/dev/null || echo "(empty)"
    echo ""
    echo "=== MONITOR LOG ==="
    cat "$ANALYSIS_DIR/${RUN_LABEL}-monitor.log" 2>/dev/null || echo "(empty)"
    echo ""
    echo "=== JAMT LOG ==="
    cat "$ANALYSIS_DIR/${RUN_LABEL}-jamt.log" 2>/dev/null || echo "(empty)"
    echo ""
    echo "=== NODE LOG ERRORS AND PANICS ==="
    grep -E "\[ERROR\]|\[WARNING\]|Panic|Traceback|PAGE_FAULT|HOST\(12\)|Invoke outcome" "$LOG_FILE" | head -150
    echo ""
    echo "=== HOST CALL FREQUENCY ==="
    grep -oP 'HOST\(\K\d+' "$LOG_FILE" | sort -n | uniq -c | sort -rn | head -20
    echo ""
    echo "=== REFINEMENT SEQUENCE (first refining node, last 80 lines of HOST 10/11/12) ==="
    grep -E "HOST\(10\)|HOST\(11\)|HOST\(12\)|Invoke outcome|Page fault at|PVM result.*final_pc" "$LOG_FILE" | head -80
} > "$EXCERPT"

DEEP_REPORT="$ANALYSIS_DIR/${RUN_LABEL}-deep-analysis.txt"

claude -p "You are analyzing a PolkaDoom testnet run on Tessera (Python JAM protocol node).

## Context
- Tessera runs 6 validator nodes in tmux
- jamt creates a CoreVM service for doom
- corevm-builder submits work packages that run doom inside a PVM
- corevm-monitor should render video frames from accumulated state
- The inner PVM (doom binary) runs inside an outer PVM (corevm engine)
- HOST(12) in refine_fns.py invokes the inner PVM
- Page faults are handled by HOST(10) poke + HOST(11) pages + HOST(12) invoke

## Key code paths
- jam/execution/invocations/functions/refine_fns.py — HOST 6-13 (refine functions)
- jam/execution/host_call.py — PsiH outer PVM execution loop
- deps/tsrkit-pvm/tsrkit_pvm/common/status.py — ExecutionStatus enum (PAGE_FAULT/HOST mutate shared state)

## Known bugs from previous analysis
1. U64 type contamination: refine_fns.py:263 creates U64 objects instead of int for inner PVM registers
2. Global state mutation: status.py PAGE_FAULT()/HOST() mutate shared enum ExecValue.register
3. Wrong validator assignment: assignment.py rotation calculation differs between block author and validators

## Your task
Analyze this specific run's logs deeply. Compare Tessera's behavior with what the reference corevm-builder produces. Find the exact point of failure, identify root causes, and provide specific code fixes.

## Log data
$(<"$EXCERPT")

Provide your analysis in this format:
1. EXECUTION SUMMARY — what happened in this run
2. FAILURE POINT — exact moment and location of failure
3. ROOT CAUSES — ranked by likelihood, with file:line references
4. SPECIFIC FIXES — exact code changes needed (show before/after)
5. VERIFICATION — how to verify each fix works" \
    --allowedTools "Read Grep Glob Bash(grep:*) Bash(wc:*) Bash(python3:*)" \
    > "$DEEP_REPORT" 2>/dev/null

echo ""
echo "================================================================"
echo "  DEEP ANALYSIS COMPLETE"
echo "================================================================"
echo ""
cat "$DEEP_REPORT"
echo ""
echo "================================================================"
echo "  FILES"
echo "================================================================"
echo "  Node logs:     $LOG_FILE"
echo "  Auto scan:     $REPORT"
echo "  Deep analysis: $DEEP_REPORT"
echo "  Builder log:   $ANALYSIS_DIR/${RUN_LABEL}-builder.log"
echo "  Monitor log:   $ANALYSIS_DIR/${RUN_LABEL}-monitor.log"
echo "================================================================"
echo ""

# ── Phase 4: Ask to apply fixes ──────────────────────────────
echo "Would you like to apply the suggested fixes? [y/N]"
read -r APPLY
if [[ "$APPLY" =~ ^[Yy] ]]; then
    echo ""
    echo "[agent] Invoking Claude to apply fixes..."
    claude -p "Read the deep analysis at $DEEP_REPORT and apply ALL the specific fixes mentioned in the SPECIFIC FIXES section. Make the minimal code changes needed. Do NOT commit to git. Do NOT modify any .planning/ or .gsd files. After applying, show a summary of what was changed." \
        --allowedTools "Read Edit Bash(python3:*) Grep Glob"
else
    echo ""
    echo "[agent] Skipped. To apply fixes later, run:"
    echo "  claude -p 'Read $DEEP_REPORT and apply the SPECIFIC FIXES section' --allowedTools 'Read Edit Grep Glob'"
fi

# Cleanup
rm -f "$RUNNER_LOG" "$EXCERPT"
