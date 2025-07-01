#!/usr/bin/env bash
set -euo pipefail

SESSION="polkajam-testnet"
TMUXP_CONFIG=".tmuxp/testnet.yaml"


start_testnet() {
  if [[ $# -lt 1 ]]; then
    echo "Usage: $0 start <path_to_polkajam>"
    exit 1
  fi
  POLKAJAM_BIN="$1"

  # Check if session already exists
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Testnet session '$SESSION' already exists."
    echo "Attach to it with: tmux attach -t $SESSION"
    echo "Or stop it with: $0 stop"
    exit 1
  fi

  echo "Starting testnet session '$SESSION'..."

  # Load tmuxp config
  POLKAJAM="$POLKAJAM_BIN" tmuxp load "$TMUXP_CONFIG"

  echo "Testnet started in background. To attach: tmux attach -t $SESSION"
}

stop_testnet() {
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Stopping testnet session '$SESSION'..."
    tmux kill-session -t "$SESSION"
    echo "Session stopped."
  else
    echo "Testnet session '$SESSION' not found."
  fi
}

# --- Main Logic ---

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 {start|stop|restart} [path_to_polkajam]"
  echo "  start   <path_to_polkajam>  - Start the testnet."
  echo "  stop                        - Stop the testnet."
  echo "  restart <path_to_polkajam>  - Restart the testnet."
  exit 1
fi

ACTION="$1"
shift

case "$ACTION" in
  start)
    start_testnet "$@"
    ;;
  stop)
    stop_testnet
    ;;
  restart)
    stop_testnet
    # Give it a moment to die
    sleep 1
    start_testnet "$@"
    ;;
  *)
    echo "Invalid command: $ACTION"
    echo "Usage: $0 {start|stop|restart} [path_to_polkajam]"
    exit 1
    ;;
esac
