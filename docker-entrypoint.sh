#!/bin/sh
set -e

export PYTHONUNBUFFERED=1

echo "[INFO] Clearing Database..."
rm -rf /app/data/*

echo "[INFO] Setting up RocksDB library for bundling..."
./setup-rocksdb.sh

start() {
  envfile="$1"
  echo "[entrypoint] starting: uv run jam --env $envfile"
  uv run jam --env "$envfile" &
}

start envs/40000.env
start envs/40001.env
start envs/40002.env
start envs/40003.env
start envs/40004.env
start envs/40005.env

wait
