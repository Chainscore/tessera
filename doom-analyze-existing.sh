#!/usr/bin/env bash
# doom-analyze-existing.sh — Analyze existing test-logs/ files
# Usage: ./doom-analyze-existing.sh [start_num] [end_num]
#   Analyzes logs from l<start>.txt to l<end>.txt
#   Default: analyze all existing logs
set -uo pipefail

TESSERA_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$TESSERA_DIR/test-logs"
ANALYSIS_DIR="$TESSERA_DIR/test-analysis"

START="${1:-0}"
END="${2:-999}"

mkdir -p "$ANALYSIS_DIR"

echo "Analyzing existing logs from l${START}.txt to l${END}.txt..."

ANALYZED=0
for f in "$LOG_DIR"/l*.txt; do
    [ -e "$f" ] || continue
    base="$(basename "$f" .txt)"
    num="${base#l}"
    [[ "$num" =~ ^[0-9]+$ ]] || continue
    [ "$num" -ge "$START" ] && [ "$num" -le "$END" ] || continue

    echo "Analyzing $base..."
    "$TESSERA_DIR/doom-analyze.sh" "$f" "$base" "" "" "" >/dev/null 2>&1
    ANALYZED=$((ANALYZED + 1))
done

echo "Analyzed $ANALYZED log files."
echo ""

# Quick summary across all analyzed
echo "── Cross-run issue summary ──"
for issue_type in INVALID_BLOCKS EPOCH_ERROR NO_REFINE BUILDER_NODE_ERROR NO_WP PYTHON_EXCEPTION MEMORY; do
    COUNT=0
    TOTAL=0
    for f in "$ANALYSIS_DIR"/l*-analysis.txt; do
        [ -e "$f" ] || continue
        TOTAL=$((TOTAL + 1))
        if grep -q "$issue_type" "$f" 2>/dev/null; then
            COUNT=$((COUNT + 1))
        fi
    done
    if [ "$COUNT" -gt 0 ] && [ "$TOTAL" -gt 0 ]; then
        echo "  $issue_type: $COUNT / $TOTAL runs"
    fi
done
