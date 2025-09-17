#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <num_instances>"
  exit 1
fi

N="$1"
BASE_PORT=40000
THEMES=(matrix polkadot default)  # cycle themes if n > 3
SESSION="testnet"

# Start tmux session
tmux new-session -d -s "$SESSION"

for ((i=0; i<N; i++)); do
  PORT=$((BASE_PORT + i))
  DB="db/$PORT"
  ENV="envs/$PORT.env"
  THEME="${THEMES[i % ${#THEMES[@]}]}"
  CMD="uv run jam --env \"$ENV\" --db \"$DB\" --theme \"$THEME\" --start-genesis --validator"

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
