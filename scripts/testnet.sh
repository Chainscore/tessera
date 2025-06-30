#!/usr/bin/env bash
set -euo pipefail

SESSION="polkajam-testnet"

start_testnet() {
  local POLKAJAM_BIN
  if [[ $# -lt 1 ]]; then
    echo "Usage: $0 start <path_to_polkajam>"
    exit 1
  fi
  POLKAJAM_BIN="$1"

  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists. attach with   tmux a -t $SESSION"
    exit 1
  fi

  echo "Creating session '$SESSION'…"
  tmux new-session   -d \
                    -s "$SESSION" \
                    -n main \
                    "$SHELL"

  # split off the RIGHT 30% for jam
  tmux split-window  -h -p 30 \
                    -t "$SESSION:main.0"

  # send your poetry/jam command to that right-hand pane
  tmux send-keys     -t "$SESSION:main.1" \
                    "poetry run jam --start-genesis --validator --theme 'matrix' --env 'envs/40001.env'" C-m

  # now WORK ON THE LEFT PANE ONLY:
  local LEFT_TOP="${SESSION}:main.0"

  # create 4 additional vertical splits under the top-left pane,
  # so you end up with 5 total on the left
  for _ in {1..4}; do
    tmux split-window -v -t "$LEFT_TOP"
  done

  # rebalance all panes in the window so left side is 5 equal heights, right is full height
  tmux select-layout -t "$SESSION:main" even-vertical

  # send your polkajam commands
  # left panes will be indexes 0,2,3,4,5  (right is 1)
  local validators=(0 2 3 4 5)
  for i in "${!validators[@]}"; do
    tmux send-keys -t "$SESSION:main.${validators[$i]}" \
      "$POLKAJAM_BIN run --dev-validator ${validators[$i]} -t --rpc-port 0" C-m
  done

  # finally, drop you into the JAM pane
  tmux select-pane -t "$SESSION:main.1"

  echo "Started.  tmux a -t $SESSION"
}

stop_testnet() {
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
    echo "Session '$SESSION' killed."
  else
    echo "No session '$SESSION' found."
  fi
}

if (( $# < 1 )); then
  echo "Usage: $0 {start|stop|restart} [path_to_polkajam]"
  exit 1
fi

case "$1" in
  start)   shift; start_testnet "$@"   ;;
  stop)    stop_testnet                ;;
  restart) stop_testnet; sleep 1; shift; start_testnet "$@" ;;
  *)       echo "Unknown command: $1"; exit 1 ;;
esac

