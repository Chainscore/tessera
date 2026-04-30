#!/usr/bin/env bash

set -euo pipefail

MODULES=(
  fallback
  fuzzy
  fuzzy_light
  preimages
  preimages_light
  safrole
  storage
  storage_light
)

PATTERN="${PATTERN:-*.bin}"
LOG_LEVEL="${JAM_LOG_LEVEL:-debug}"
TMP_BASE="${TMPDIR:-$HOME/tmpjam}"
SELECTED_MODULE="${MODULE:-all}"

if [[ "${SELECTED_MODULE}" != "all" ]]; then
  MODULES=("${SELECTED_MODULE}")
fi

mkdir -p "${TMP_BASE}"

for module in "${MODULES[@]}"; do
  echo "== ${module} =="
  TMPDIR="${TMP_BASE}" ASYNC=1 JAM_LOG_LEVEL="${LOG_LEVEL}" \
    uv run pytest test-suites/harness/w3f/traces/test_traces_linear_unified.py \
    --module "${module}" \
    --pattern "${PATTERN}" \
    --no-rpc \
    -s -vvv
done
