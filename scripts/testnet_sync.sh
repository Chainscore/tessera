#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <num_instances>"
  exit 1
fi

N="$1"
BASE_PORT=40000
PIDS=()
THEMES=(matrix polkadot default noir solarized monokai)

for ((i=0; i<N; i++)); do
  PORT=$((BASE_PORT + i))
  DB="db/$PORT"
  ENV="envs/$PORT.env"
  THEME="${THEMES[i % ${#THEMES[@]}]}"
  echo "Launching validator $i on port $PORT with theme $THEME"
  if [[ $i -eq 0 ]]; then
    poetry run jam --env "$ENV" --db "$DB" --theme "$THEME" --start-genesis --validator &
    sleep 10 &
  else
    poetry run jam --env "$ENV" --db "$DB" --theme "$THEME" --validator &
  fi
  PIDS+=($!)
done

trap "kill ${PIDS[*]}; exit" INT TERM

echo "Launched Tessera Testnet (Processes: ${PIDS[*]})"
wait "${PIDS[@]}"
