#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path_to_polkajam>"
  exit 1
fi

POLKAJAM_BIN="$1"
SESSION="polkajam-testnet"

# Commands for each validator
COMMANDS=(
  "$POLKAJAM_BIN run --dev-validator 0 -t --rpc-port 0"
  "poetry run jam --start-genesis --validator --theme 'matrix' --env 'envs/40001.env'"
  "$POLKAJAM_BIN run --dev-validator 2 -t --rpc-port 0"
  "$POLKAJAM_BIN run --dev-validator 3 -t --rpc-port 0"
  "$POLKAJAM_BIN run --dev-validator 4 -t --rpc-port 0"
  "$POLKAJAM_BIN run --dev-validator 5 -t --rpc-port 0"
)

# Start tmux session
tmux new-session -d -s "$SESSION"

# Launch validators in tmux panes
for i in "${!COMMANDS[@]}"; do
  CMD="${COMMANDS[$i]}"
  if (( i == 0 )); then
    # Send first command to original pane
    tmux send-keys -t "$SESSION":0 "$CMD" C-m
  else
    # Split a new pane for each validator (horizontally)
    tmux split-window -t "$SESSION":0 -h
    tmux send-keys -t "$SESSION":0.$i "$CMD" C-m
    tmux select-layout -t "$SESSION":0 tiled  # Rearrange panes
  fi
done

tmux select-layout -t "$SESSION":0 tiled
tmux attach -t "$SESSION"
