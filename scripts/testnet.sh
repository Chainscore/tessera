#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path_to_polkajam>"
  exit 1
fi

POLKAJAM_BIN="$1"
SESSION="polkajam-net"

# 1) Tear down any existing session
tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION"

# 2) Start a fresh session
tmux new-session -d -s "$SESSION" -n network

# 3) Carve off rightmost 30% for uv/jam
UV_IDX=$(tmux split-window -h -p 30 -t "${SESSION}:network.0" -P -F "#{pane_index}")
tmux send-keys -t "${SESSION}:network.${UV_IDX}" \
  "uv run jam --start-genesis --validator --theme 'matrix' --env 'envs/40001.env'" C-m

# 4) Carve off middle 30% for validator 5
MIDDLE_IDX=$(tmux split-window -h -p 30 -t "${SESSION}:network.0" -P -F "#{pane_index}")
tmux send-keys -t "${SESSION}:network.${MIDDLE_IDX}" \
  "$POLKAJAM_BIN run --dev-validator 5 -t --rpc-port 0" C-m

# 5) Split the leftover ~40% pane (always pane 0) into four equal-ish rows
LEFT0=0
# first split: bottom 75% → L1, top 25% remains in LEFT0
L1=$(tmux split-window -v -p 75 -t "${SESSION}:network.${LEFT0}" -P -F "#{pane_index}")
# second split: split L1 into top ~66% → L2, bottom ~34% remains in L1
L2=$(tmux split-window -v -p 66 -t "${SESSION}:network.${L1}" -P -F "#{pane_index}")
# third split: split L2 into top 50% → L3, bottom 50% remains in L2
L3=$(tmux split-window -v -p 50 -t "${SESSION}:network.${L2}" -P -F "#{pane_index}")

# map them in top-to-bottom order:
ROW1=${LEFT0}   # top ~25%
ROW2=${L3}      # next ~25%
ROW3=${L2}      # next ~25%
ROW4=${L1}      # bottom ~25%

# 6) Dispatch validators into the four rows
tmux send-keys -t "${SESSION}:network.${ROW1}" \
  "$POLKAJAM_BIN run --dev-validator 0 -t --rpc-port 0" C-m
tmux send-keys -t "${SESSION}:network.${ROW2}" \
  "$POLKAJAM_BIN run --dev-validator 2 -t --rpc-port 0" C-m
tmux send-keys -t "${SESSION}:network.${ROW3}" \
  "$POLKAJAM_BIN run --dev-validator 3 -t --rpc-port 0" C-m
tmux send-keys -t "${SESSION}:network.${ROW4}" \
  "$POLKAJAM_BIN run --dev-validator 4 -t --rpc-port 0" C-m

# 7) Attach so you see all six panes running
tmux attach -t "$SESSION"

