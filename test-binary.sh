#!/bin/bash
set -e

# Configuration
CONTAINER_NAME="tessera-fuzzer"
IMAGE_NAME="tessera-node:fuzzer"
TARGET_SOCK="/tmp/tessera_fuzzer.sock"
VECTOR_PATH=${2:-"storage"}  # Default to "storage" if not provided
DURATION=${1:-60}

# JAM-spec Docker performance args (identical to conformance script)
DOCKER_ARGS="--rm --name $CONTAINER_NAME --user $(id -u):$(id -g) --platform linux/amd64 --cpuset-cpus=0-17 --cpu-shares=2048 --memory=8g --memory-swap=8g --shm-size=1g --ulimit nofile=65536:65536 --ulimit nproc=32768:32768 --sysctl net.core.somaxconn=65535 --sysctl net.ipv4.tcp_tw_reuse=1 --security-opt seccomp=unconfined --security-opt apparmor=unconfined --cap-add=SYS_NICE --cap-add=SYS_RESOURCE --cap-add=IPC_LOCK -v /tmp:/tmp -v $PWD/dist:/tessera -v $PWD/test-suites/ext/jam-conformance/test-vectors/traces:/test-vectors -w /tessera"

cleanup() {
    docker kill $CONTAINER_NAME 2>/dev/null || true
    rm -f $TARGET_SOCK
}
trap cleanup EXIT INT TERM

case "${1:-test}" in
    "build")
        docker build -f Dockerfile.tessera-bin-test -t $IMAGE_NAME .
        ;;
    "test")
        echo "Testing tessera-node with vector path: $VECTOR_PATH"
        sudo chrt -f 99 nice -n -20 ionice -c1 -n0 taskset -c 0-32 \
        docker run $DOCKER_ARGS $IMAGE_NAME ./tessera-node --import /test-vectors/$VECTOR_PATH
        ;;
    "clean")
        cleanup
        docker rmi $IMAGE_NAME 2>/dev/null || true
        rm -f Dockerfile.tessera
        ;;
    *)
        echo "Usage: $0 [build|test|clean] [duration_seconds] [vector_path]"
        echo "Example: $0 test 120 storage"
        echo "Example: $0 test 60 refine"
        echo "Default vector_path: storage"
        ;;
esac