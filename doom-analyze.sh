#!/usr/bin/env bash
# doom-analyze.sh — Deep log analysis for PolkaDoom testnet runs
# Usage: ./doom-analyze.sh <log_file> <run_label> [builder_log] [monitor_log] [jamt_log]
# Outputs a comprehensive analysis report to test-analysis/<run_label>-analysis.txt
set -uo pipefail

TESSERA_DIR="$(cd "$(dirname "$0")" && pwd)"
ANALYSIS_DIR="$TESSERA_DIR/test-analysis"

LOG_FILE="${1:?Usage: doom-analyze.sh <log_file> <run_label>}"
RUN_LABEL="${2:?Usage: doom-analyze.sh <log_file> <run_label>}"
BUILDER_LOG="${3:-$ANALYSIS_DIR/${RUN_LABEL}-builder.log}"
MONITOR_LOG="${4:-$ANALYSIS_DIR/${RUN_LABEL}-monitor.log}"
JAMT_LOG="${5:-$ANALYSIS_DIR/${RUN_LABEL}-jamt.log}"

REPORT="$ANALYSIS_DIR/${RUN_LABEL}-analysis.txt"
mkdir -p "$ANALYSIS_DIR"

# ── Helper functions ─────────────────────────────────────────
section() { printf '\n%s\n%s\n' "══════════════════════════════════════════════════════════════" "$1"; }
subsect() { printf '\n── %s ──\n' "$1"; }

{
section "DOOM TESTNET ANALYSIS REPORT"
echo "Run Label  : $RUN_LABEL"
echo "Log File   : $LOG_FILE"
echo "Timestamp  : $(date -Iseconds)"
echo "Builder Log: $BUILDER_LOG"
echo "Monitor Log: $MONITOR_LOG"

# ── 1. Basic health ─────────────────────────────────────────
section "1. TESTNET HEALTH"

if [ ! -f "$LOG_FILE" ]; then
    echo "ERROR: Log file not found: $LOG_FILE"
    exit 1
fi

echo "Log file size: $(wc -c < "$LOG_FILE") bytes, $(wc -l < "$LOG_FILE") lines"

# Count nodes that produced output
NODE_COUNT=0
for name in alice bob charlie dave eve fergie; do
    if grep -q "^.*$name.*\]" "$LOG_FILE"; then
        NODE_COUNT=$((NODE_COUNT + 1))
    fi
done
echo "Nodes with output: $NODE_COUNT / 6"

# Check for errors across all nodes
subsect "ERROR messages"
grep -i "\[ERROR\]" "$LOG_FILE" | head -30 || echo "(none)"

subsect "PANIC / crash messages"
grep -iE "(PANIC|Traceback|Exception|FATAL|segfault)" "$LOG_FILE" | head -20 || echo "(none)"

subsect "WARNING messages (sample)"
grep -i "\[WARNING\]" "$LOG_FILE" | head -20 || echo "(none)"

# ── 2. Network connectivity ─────────────────────────────────
section "2. NETWORK CONNECTIVITY"

subsect "Protocol negotiations"
grep -c "Negotiated protocol" "$LOG_FILE" || echo "0"

subsect "Connection issues"
grep -iE "(connection.*refused|connection.*reset|timeout|disconnect)" "$LOG_FILE" | head -10 || echo "(none)"

subsect "Validator connectivity (last status)"
# Extract the last status display for each node
for name in alice bob charlie dave eve fergie; do
    LAST_UP=$(grep "$name.*validators.*up" "$LOG_FILE" | tail -1)
    if [ -n "$LAST_UP" ]; then
        echo "  $name: $LAST_UP"
    fi
done

# ── 3. Block production ─────────────────────────────────────
section "3. BLOCK PRODUCTION"

subsect "Blocks finalized"
FINALIZED=$(grep -c "Finalized" "$LOG_FILE")
echo "Total finalized messages: $FINALIZED"

subsect "Block production timeline (first 10)"
grep "Finalized" "$LOG_FILE" | head -10

subsect "Slot progression"
# Extract slot numbers
SLOTS=$(grep -oP 'Slot\s+\K\d+' "$LOG_FILE" | sort -n | uniq)
if [ -n "$SLOTS" ]; then
    FIRST_SLOT=$(echo "$SLOTS" | head -1)
    LAST_SLOT=$(echo "$SLOTS" | tail -1)
    SLOT_COUNT=$(echo "$SLOTS" | wc -l)
    echo "First slot: $FIRST_SLOT"
    echo "Last slot : $LAST_SLOT"
    echo "Unique slots seen: $SLOT_COUNT"
    echo "Slot range: $((LAST_SLOT - FIRST_SLOT))"
fi

# ── 4. Service creation (bootstrap) ─────────────────────────
section "4. SERVICE CREATION (BOOTSTRAP)"

subsect "NEW SERVICE messages"
grep -i "NEW SERVICE" "$LOG_FILE" | head -10 || echo "(none)"

subsect "Bootstrap accumulate"
grep -i "Bootstrap.*Accumulate" "$LOG_FILE" | head -10 || echo "(none)"

subsect "Service transfers"
grep -i "Transferred" "$LOG_FILE" | head -10 || echo "(none)"

# ── 5. Refinement analysis (THE KEY SECTION) ────────────────
section "5. REFINEMENT ANALYSIS"

subsect "Work packages received"
grep -i "Received.*Work.*Report\|work.package.*received\|Guaranteed.*Work" "$LOG_FILE" | head -20 || echo "(none)"

subsect "Refinement host calls (from node logs)"
# Count each host call type during refinement
echo "Host call frequency:"
grep -oP 'HOST\(\K\d+' "$LOG_FILE" | sort -n | uniq -c | sort -rn | head -20 || echo "(none)"

subsect "Page fault handling"
grep -i "page.fault\|PAGE_FAULT" "$LOG_FILE" | wc -l | xargs -I{} echo "Page fault count: {}"
grep -i "page.fault\|PAGE_FAULT" "$LOG_FILE" | head -10

subsect "PVM execution issues"
grep -iE "(OOM|OOB|out.of.memory|out.of.bounds|overflow|underflow)" "$LOG_FILE" | head -10 || echo "(none)"

subsect "Refinement gas usage"
grep -i "gas" "$LOG_FILE" | grep -i "refin" | head -10 || echo "(none)"

subsect "sbrk calls"
grep -i "sbrk" "$LOG_FILE" | head -10 || echo "(none)"

subsect "HOST(6) through HOST(13) — Refine host calls"
for h in 6 7 8 9 10 11 12 13; do
    COUNT=$(grep -c "HOST($h)" "$LOG_FILE")
    echo "  HOST($h): $COUNT calls"
done

subsect "HOST(11) — alter_accessibility"
grep "HOST(11)" "$LOG_FILE" | head -5

subsect "HOST(12) — invoke (nested PVM)"
grep "HOST(12)" "$LOG_FILE" | head -5

# ── 6. Work report validation ───────────────────────────────
section "6. WORK REPORT VALIDATION"

subsect "Invalid block messages"
grep -i "Invalid block\|invalid.*report\|report.*invalid" "$LOG_FILE" | head -20 || echo "(none)"

subsect "Report epoch issues"
grep -i "report_epoch\|epoch.*before\|epoch.*error" "$LOG_FILE" | head -10 || echo "(none)"

subsect "Assurance messages"
grep -i "assur" "$LOG_FILE" | head -10 || echo "(none)"

# ── 7. Builder analysis ─────────────────────────────────────
section "7. COREVM-BUILDER ANALYSIS"

if [ -f "$BUILDER_LOG" ] && [ -s "$BUILDER_LOG" ]; then
    echo "Builder log size: $(wc -l < "$BUILDER_LOG") lines"

    subsect "Builder steps"
    grep -i "Step\|step" "$BUILDER_LOG" | head -10

    subsect "Page faults in builder"
    BUILDER_PF=$(grep -c "PageFault" "$BUILDER_LOG")
    echo "Page faults: $BUILDER_PF"

    subsect "Host call faults in builder"
    grep -c "HostCallFault" "$BUILDER_LOG" | xargs -I{} echo "Host call faults: {}"

    subsect "Video frames produced"
    FRAMES=$(grep -c "yield_video_frame" "$BUILDER_LOG")
    echo "Video frames: $FRAMES"

    subsect "Console output from Doom"
    grep "yield_console_data.*utf8=Ok" "$BUILDER_LOG" | grep -oP 'utf8=Ok\("\K[^"]*' | head -20

    subsect "Builder outcome"
    grep -iE "(TimeLimitReached|outcome|submitted|error|failed|Node error)" "$BUILDER_LOG" | tail -10

    subsect "Work package submission"
    grep -i "submit\|work.package" "$BUILDER_LOG" | tail -5

    subsect "Memory pages exported"
    grep "Exported.*page" "$BUILDER_LOG" | tail -5
    EXPORT_COUNT=$(grep -c "Exported regular page" "$BUILDER_LOG")
    echo "Total pages exported: $EXPORT_COUNT"
else
    echo "Builder log not found or empty"
fi

# ── 8. Monitor analysis ─────────────────────────────────────
section "8. COREVM-MONITOR ANALYSIS"

if [ -f "$MONITOR_LOG" ] && [ -s "$MONITOR_LOG" ]; then
    echo "Monitor log size: $(wc -l < "$MONITOR_LOG") lines"
    subsect "Monitor output"
    cat "$MONITOR_LOG" | head -30
    subsect "Frames rendered"
    grep -c "frame\|Frame\|render" "$MONITOR_LOG" | xargs -I{} echo "Frame-related messages: {}"
else
    echo "Monitor log not found or empty — NO FRAMES RENDERED"
fi

# ── 9. Comparison: Tessera vs expected behavior ──────────────
section "9. TESSERA vs EXPECTED BEHAVIOR"

echo "Expected flow:"
echo "  1. Service created via bootstrap accumulate"
echo "  2. corevm-builder submits WP with doom refinement"
echo "  3. Tessera nodes refine the WP (hundreds of page faults + host calls)"
echo "  4. Work report generated, guaranteed, and reported"
echo "  5. Accumulate runs, writing state"
echo "  6. corevm-monitor reads accumulate output and renders frames"
echo ""

# Check each step
echo "Step analysis:"

# Step 1: Service creation
SVC_CREATED=$(grep -c "NEW SERVICE CREATED" "$LOG_FILE")
echo "  [$([ "$SVC_CREATED" -gt 0 ] && echo 'OK' || echo 'FAIL')] Service creation: $SVC_CREATED services created"

# Step 2: WP submission
WP_RECEIVED=$(grep -c "Received.*Work.*Report\|Guaranteed.*Work" "$LOG_FILE")
echo "  [$([ "$WP_RECEIVED" -gt 0 ] && echo 'OK' || echo 'FAIL')] Work package received: $WP_RECEIVED"

# Step 3: Refinement
REFINE_HOSTS=$(grep -c "HOST(12)" "$LOG_FILE")
echo "  [$([ "$REFINE_HOSTS" -gt 0 ] && echo 'OK' || echo 'FAIL')] Refinement HOST(12) invoke calls: $REFINE_HOSTS"

# Step 4: Work report
WR_HASH=$(grep -oP 'wr_hash=\K[a-f0-9]+' "$LOG_FILE" | head -1)
echo "  [$([ -n "$WR_HASH" ] && echo 'OK' || echo 'FAIL')] Work report hash: ${WR_HASH:-(none)}"

# Step 5: Accumulate
ACCUM=$(grep -c "Accumulate\|accumulate" "$LOG_FILE")
echo "  [$([ "$ACCUM" -gt 0 ] && echo 'OK' || echo 'FAIL')] Accumulate messages: $ACCUM"

# Step 6: Monitor frames
if [ -f "$MONITOR_LOG" ] && [ -s "$MONITOR_LOG" ]; then
    MON_FRAMES=$(grep -c "frame\|Frame\|render" "$MONITOR_LOG")
    echo "  [$([ "$MON_FRAMES" -gt 0 ] && echo 'OK' || echo 'FAIL')] Monitor frames: $MON_FRAMES"
else
    echo "  [FAIL] Monitor: no output"
fi

# ── 10. Root cause candidates ────────────────────────────────
section "10. ROOT CAUSE CANDIDATES"

echo "Analyzing failure patterns..."
echo ""

# Check for common failure modes
ISSUES=()

# Issue: Invalid block errors
INVALID_BLOCKS=$(grep -c "\[ERROR\].*Invalid block" "$LOG_FILE")
if [ "$INVALID_BLOCKS" -gt 0 ]; then
    ISSUES+=("INVALID_BLOCKS: $INVALID_BLOCKS invalid block errors detected")
    echo "ISSUE: Invalid blocks ($INVALID_BLOCKS)"
    grep "\[ERROR\].*Invalid block" "$LOG_FILE" | head -5
    echo ""
fi

# Issue: Report epoch issues
EPOCH_ERR=$(grep -c "report_epoch" "$LOG_FILE")
if [ "$EPOCH_ERR" -gt 0 ]; then
    ISSUES+=("EPOCH_ERROR: Report epoch validation failures ($EPOCH_ERR)")
    echo "ISSUE: Report epoch errors ($EPOCH_ERR)"
    grep "report_epoch" "$LOG_FILE" | head -5
    echo ""
fi

# Issue: No refinement happening
if [ "$REFINE_HOSTS" -eq 0 ] && [ "$WP_RECEIVED" -gt 0 ]; then
    ISSUES+=("NO_REFINE: Work packages received but no refinement HOST(12) calls")
    echo "ISSUE: Work packages received but refinement not executing"
    echo ""
fi

# Issue: Builder error
if [ -f "$BUILDER_LOG" ]; then
    NODE_ERR=$(grep -c "Node error" "$BUILDER_LOG")
    if [ "$NODE_ERR" -gt 0 ]; then
        ISSUES+=("BUILDER_NODE_ERROR: Builder received node errors")
        echo "ISSUE: Builder received node errors"
        grep "Node error" "$BUILDER_LOG"
        echo ""
    fi
fi

# Issue: No WP received at all
if [ "$WP_RECEIVED" -eq 0 ]; then
    ISSUES+=("NO_WP: No work packages received by any node")
    echo "ISSUE: No work packages received"
    echo ""
fi

# Issue: Traceback / Python exception
TB=$(grep -c "Traceback" "$LOG_FILE")
if [ "$TB" -gt 0 ]; then
    ISSUES+=("PYTHON_EXCEPTION: $TB tracebacks in node logs")
    echo "ISSUE: Python exceptions ($TB tracebacks)"
    grep -A5 "Traceback" "$LOG_FILE" | head -30
    echo ""
fi

# Issue: PVM memory issues
MEM_ISSUES=$(grep -c "OOM\|OOB\|out.of.memory\|MemoryError" "$LOG_FILE")
if [ "$MEM_ISSUES" -gt 0 ]; then
    ISSUES+=("MEMORY: PVM memory issues ($MEM_ISSUES)")
    echo "ISSUE: PVM memory issues ($MEM_ISSUES)"
    grep -iE "OOM|OOB|out.of.memory|MemoryError" "$LOG_FILE" | head -10
    echo ""
fi

if [ ${#ISSUES[@]} -eq 0 ]; then
    echo "No obvious failure patterns detected in logs."
    echo "Possible causes:"
    echo "  - Timing issue (testnet not ready when builder connects)"
    echo "  - Refinement output mismatch (Tessera produces different result than expected)"
    echo "  - Accumulate logic difference from reference implementation"
fi

# ── Summary ──────────────────────────────────────────────────
section "SUMMARY"
echo "Issues found: ${#ISSUES[@]}"
for issue in "${ISSUES[@]:-}"; do
    echo "  - $issue"
done
echo ""
echo "Builder produced $([ -f "$BUILDER_LOG" ] && grep -c "yield_video_frame" "$BUILDER_LOG" || echo 0) video frames"
echo "Monitor rendered $([ -f "$MONITOR_LOG" ] && wc -l < "$MONITOR_LOG" || echo 0) lines of output"
echo "Testnet processed $FINALIZED finalized blocks"

} > "$REPORT" 2>&1

echo "Analysis saved to: $REPORT"
echo "$REPORT"
