#!/bin/sh
set -eu

IMAGE_REF="${1:-chainscore/tessera:local}"
SPEC="${2:-tiny}"
CONTAINER_NAME="${3:-tessera-fuzz-test}"
CASE_COUNT="${4:-50}"
EXAMPLES_ROOT="${JAM_CONFORMANCE_EXAMPLES_ROOT:-test-suites/ext/jam-conformance/fuzz-proto/examples/0.7.2}"

DATA_DIR="$(mktemp -d /tmp/tessera-docker-data.XXXXXX)"
SOCK_DIR="$(mktemp -d /tmp/tessera-docker-sock.XXXXXX)"
SOCK_PATH="${SOCK_DIR}/jam_target.sock"

chmod 777 "${DATA_DIR}" "${SOCK_DIR}"

cleanup() {
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  docker run --rm \
    -v "${DATA_DIR}:/cleanup-data" \
    -v "${SOCK_DIR}:/cleanup-sock" \
    --entrypoint /bin/sh \
    "${IMAGE_REF}" \
    -c 'rm -rf /cleanup-data/* /cleanup-data/.[!.]* /cleanup-data/..?* /cleanup-sock/* /cleanup-sock/.[!.]* /cleanup-sock/..?*' \
    >/dev/null 2>&1 || true
  rm -rf "${DATA_DIR}" "${SOCK_DIR}"
}

trap cleanup EXIT INT TERM

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

docker run -d \
  --name "${CONTAINER_NAME}" \
  --user "$(id -u):$(id -g)" \
  -e JAM_FUZZ=1 \
  -e JAM_FUZZ_SPEC="${SPEC}" \
  -e JAM_FUZZ_DATA_PATH=/data \
  -e JAM_FUZZ_SOCK_PATH=/sock/jam_target.sock \
  -e JAM_FUZZ_LOG_LEVEL=info \
  -v "${DATA_DIR}:/data:Z" \
  -v "${SOCK_DIR}:/sock:Z" \
  "${IMAGE_REF}" >/dev/null

for _ in $(seq 1 100); do
  if [ -S "${SOCK_PATH}" ]; then
    break
  fi
  sleep 0.2
done

if [ ! -S "${SOCK_PATH}" ]; then
  echo "Socket did not appear at ${SOCK_PATH}" >&2
  docker logs "${CONTAINER_NAME}" || true
  exit 1
fi

python3 - "${SOCK_PATH}" "${CASE_COUNT}" "${EXAMPLES_ROOT}" <<'PY'
import socket
import struct
import sys
from pathlib import Path

sock_path = sys.argv[1]
case_count = int(sys.argv[2])
base_root = Path(sys.argv[3])

if not base_root.exists():
    raise SystemExit(f"examples root does not exist: {base_root}")

def send_and_recv(sock: socket.socket, payload: bytes) -> bytes:
    sock.sendall(struct.pack("<I", len(payload)))
    sock.sendall(payload)
    length = struct.unpack("<I", sock.recv(4))[0]
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise RuntimeError("connection closed while reading response")
        data += chunk
    return data

def validate_response(expected: bytes, actual: bytes, label: str) -> None:
    expected_tag = expected[0]
    actual_tag = actual[0] if actual else None

    if label.endswith("peer_info"):
        if actual_tag != 0x00:
            raise SystemExit(f"unexpected peer response tag: {actual_tag!r}")
        return

    if expected_tag == 0xFF:
        if actual_tag != 0xFF:
            raise SystemExit(f"expected error response, got tag {actual_tag!r}")
        return

    if actual != expected:
        raise SystemExit(f"response mismatch for {label}")

def run_suite(suite: str) -> None:
    base = base_root / suite
    fuzzer_files = sorted(base.glob("*_fuzzer_*.bin"))
    target_files = sorted(base.glob("*_target_*.bin"))

    if len(fuzzer_files) != len(target_files):
        raise SystemExit(f"file count mismatch in {suite}: {len(fuzzer_files)} vs {len(target_files)}")

    pairs = list(zip(fuzzer_files, target_files))[:case_count]
    if len(pairs) < case_count:
        raise SystemExit(f"{suite} only has {len(pairs)} pairs, expected at least {case_count}")

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(sock_path)

        for index, (req_file, expected_file) in enumerate(pairs, start=1):
            req = req_file.read_bytes()
            expected = expected_file.read_bytes()
            actual = send_and_recv(sock, req)
            validate_response(expected, actual, req_file.stem)
            print(f"{suite}: {index}/{case_count} ok")

run_suite("no_forks")
run_suite("forks")
print(f"Docker fuzz image protocol test passed for {case_count} no_forks and {case_count} forks pairs.")
PY
