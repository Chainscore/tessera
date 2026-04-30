#!/bin/sh
set -eu

IMAGE_NAME="${1:-chainscore/tessera}"
IMAGE_TAG="${2:-local}"
SPEC="${3:-tiny}"

DATA_DIR="${PWD}/.docker-fuzz-data"
SOCK_DIR="/tmp/tessera-sock"

mkdir -p "$DATA_DIR"
mkdir -p "$SOCK_DIR"

sudo docker rm -f tessera-fuzz >/dev/null 2>&1 || true

sudo docker run -d \
  --name tessera-fuzz \
  -e JAM_FUZZ=1 \
  -e JAM_FUZZ_SPEC="$SPEC" \
  -e JAM_FUZZ_DATA_PATH=/data \
  -e JAM_FUZZ_SOCK_PATH=/sock/jam_target.sock \
  -e JAM_FUZZ_LOG_LEVEL=info \
  -v "$DATA_DIR:/data:Z" \
  -v "$SOCK_DIR:/sock:Z" \
  "${IMAGE_NAME}:${IMAGE_TAG}"

echo
echo "Container: tessera-fuzz"
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Spec: ${SPEC}"
echo "Socket: ${SOCK_DIR}/jam_target.sock"
echo
echo "Useful commands:"
echo "  sudo docker logs -f tessera-fuzz"
echo "  ls -l ${SOCK_DIR}/jam_target.sock"
echo "  sudo docker rm -f tessera-fuzz"
