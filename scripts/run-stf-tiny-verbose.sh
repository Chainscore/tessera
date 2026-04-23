#!/usr/bin/env bash

set -euo pipefail

MODULES=(
  assurances
  authorizations
  history
  preimages
  safrole
  reports
  statistics
  disputes
  accumulate
)

SPEC="${SPEC:-tiny}"
PATTERN="${PATTERN:-*.json}"
LOG_LEVEL="${JAM_LOG_LEVEL:-debug}"

for module in "${MODULES[@]}"; do
  echo "== ${module} =="
  ASYNC=1 JAM_LOG_LEVEL="${LOG_LEVEL}" \
    uv run pytest test-suites/harness/w3f/stf/test_w3f_vectors.py \
    --module "${module}" \
    --spec "${SPEC}" \
    --pattern "${PATTERN}" \
    -s -vv --no-rpc
done
