#!/bin/sh
set -e

rm -rf /app/data/*

start() {
  envfile="$1"
  echo "[entrypoint] starting: poetry run jam --env $envfile"
  poetry run jam --env "$envfile" &
}

start envs/40000.env
start envs/40001.env
start envs/40002.env
start envs/40003.env
start envs/40004.env
start envs/40005.env

wait

# Run the app
#exec poetry run jam "$@"