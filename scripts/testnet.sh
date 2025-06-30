#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path_to_polkajam>"
  exit 1
fi

POLKAJAM_BIN="$1"
SESSION="polkajam-net"

# kill any existing session
tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION"

# create new session with one window
tmux new-session -d -s "$SESSION" -n network

# split into left and right columns
tmux split-window -h -t "${SESSION}:network.0"

# build 3 rows on left column
tmux select-pane -t "${SESSION}:network.0"
tmux split-window -v -t "${SESSION}:network.0"
tmux split-window -v -t "${SESSION}:network.2"

# build 3 rows on right column
tmux select-pane -t "${SESSION}:network.1"
tmux split-window -v -t "${SESSION}:network.1"
tmux split-window -v -t "${SESSION}:network.4"

# send commands to each pane
tmux send-keys -t "${SESSION}:network.0" \
  "$POLKAJAM_BIN run --dev-validator 0 -t --rpc-port 0" C-m

tmux send-keys -t "${SESSION}:network.2" \
  "$POLKAJAM_BIN run --dev-validator 2 -t --rpc-port 0" C-m

tmux send-keys -t "${SESSION}:network.3" \
  "$POLKAJAM_BIN run --dev-validator 3 -t --rpc-port 0" C-m

tmux send-keys -t "${SESSION}:network.1" \
  "$POLKAJAM_BIN run --dev-validator 4 -t --rpc-port 0" C-m

tmux send-keys -t "${SESSION}:network.4" \
  "$POLKAJAM_BIN run --dev-validator 5 -t --rpc-port 0" C-m

tmux send-keys -t "${SESSION}:network.5" \
  "poetry run jam --start-genesis --validator --theme 'matrix' --env 'envs/40001.env'" C-m

# attach to session
tmux attach -t "$SESSION"

