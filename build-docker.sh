#!/bin/sh
set -eu

IMAGE_NAME="${1:-chainscore/tessera}"
IMAGE_TAG="${2:-local}"

echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG} using Dockerfile..."
docker build -f Dockerfile -t "${IMAGE_NAME}:${IMAGE_TAG}" .

echo
echo "Build complete."
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo
echo "Start fuzz mode locally with:"
echo "  ./run-docker-fuzz.sh ${IMAGE_NAME} ${IMAGE_TAG} tiny"
echo
echo "Docker image modes:"
echo "  - default: normal single-node behavior using envs/40000.env"
echo "  - TESTNET=1: normal six-node testnet behavior"
echo "  - JAM_FUZZ=1: conformance target mode"
