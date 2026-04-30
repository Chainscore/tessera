# Tessera Commands

This file is a repo-local command guide for what is currently runnable in this checkout: setup, node entrypoints, tests, harnesses, perf helpers, and utility scripts.

## Prereqs

```bash
uv sync --all-extras
uv run pre-commit install
mkdir -p data
```

If you need RocksDB for bundling:

```bash
./setup-rocksdb.sh
```

## Main Entry Points

### Package entrypoint: `jam`

This is the console script defined in [`pyproject.toml`](/home/darkknight/Chainscore%20Labs/Tesseract/tessera-main/pyproject.toml).

```bash
uv run jam --help
uv run jam --env envs/40000.env
uv run jam --env envs/40000.env --validator
uv run jam --env envs/40000.env --builder
uv run jam --env envs/40000.env --db data/node-40000
uv run jam --env envs/40000.env --no-rpc
uv run jam --env envs/40000.env --telemetry host:port
```

### Alternate CLI: `jam/cli.py`

This is a separate CLI used by the standalone binary and fuzz/import flows. Its flags are not identical to `uv run jam`.

```bash
uv run python jam/cli.py --help
uv run python jam/cli.py --env envs/40000.env --db data/tmp/manual
uv run python jam/cli.py --env envs/40000.env --no-rpc
uv run python jam/cli.py --fuzzer --socket /tmp/jam_target.sock
uv run python jam/cli.py --import test-suites/ext/jam-conformance/test-vectors/traces/storage
```

## Build And QA

### Makefile

```bash
make setup
make test
make lint
make format
make clean
```

### Poe tasks

```bash
uv run poe setup
uv run poe build
uv run poe test
uv run poe lint
uv run poe format
uv run poe update-deps
```

## Binary Build

```bash
./build-binary.sh
./dist/tessera-node --help
```

## Docker Images

### Fuzz image build

The publishable conformance image is built from `Dockerfile.fuzz`, not the main `Dockerfile`.

Helper script:

```bash
sudo ./build-docker.sh
sudo ./build-docker.sh chainscore/tessera local
```

Raw build:

```bash
sudo docker build -f Dockerfile.fuzz -t chainscore/tessera:local .
```

### Fuzz image run

Helper script:

```bash
./run-docker-fuzz.sh
./run-docker-fuzz.sh chainscore/tessera local tiny
./run-docker-fuzz.sh chainscore/tessera local full
```

Raw run:

```bash
mkdir -p "$PWD/.docker-fuzz-data"
mkdir -p /tmp/tessera-sock

sudo docker rm -f tessera-fuzz >/dev/null 2>&1 || true

sudo docker run -d \
  --name tessera-fuzz \
  -e JAM_FUZZ=1 \
  -e JAM_FUZZ_SPEC=tiny \
  -e JAM_FUZZ_DATA_PATH=/data \
  -e JAM_FUZZ_SOCK_PATH=/sock/jam_target.sock \
  -e JAM_FUZZ_LOG_LEVEL=info \
  -v "$PWD/.docker-fuzz-data:/data:Z" \
  -v /tmp/tessera-sock:/sock:Z \
  chainscore/tessera:local
```

Inspect and stop:

```bash
sudo docker logs -f tessera-fuzz
ls -l /tmp/tessera-sock/jam_target.sock
sudo docker rm -f tessera-fuzz
```

Protocol smoke test against a built local image:

```bash
chmod +x scripts/test-docker-fuzz-image.sh
./scripts/test-docker-fuzz-image.sh chainscore/tessera:local tiny tessera-fuzz-test
```

Run a larger protocol regression against 50 `no_forks` and 50 `forks` pairs:

```bash
chmod +x scripts/test-docker-fuzz-image.sh
./scripts/test-docker-fuzz-image.sh chainscore/tessera:local tiny tessera-fuzz-test 50
```

### Normal mode from the same fuzz image

`Dockerfile.fuzz` is dual-mode:

- default entrypoint behavior: normal multi-node startup
- `JAM_FUZZ=1`: conformance target mode

Run normal mode:

```bash
sudo docker run --rm chainscore/tessera:local
```

### Published image names

- On release tags like `v0.7.2`: `ghcr.io/chainscore/tessera:v0.7.2`
- On release tags like `v0.7.2`: `ghcr.io/chainscore/tessera:latest`
- On `workflow_dispatch` runs without a tag: the workflow uses the resolved version string for the image tag

### Simulating the conformance workflow locally

Start the target image:

```bash
./run-docker-fuzz.sh chainscore/tessera local tiny
```

Then point `minifuzz` at the host-visible socket:

```bash
python3 ../tessera-doom/test-suites/ext/jam-conformance/fuzz-proto/minifuzz/minifuzz.py \
  -d "/home/darkknight/Chainscore Labs/Tesseract/tessera-doom/test-suites/ext/jam-conformance/fuzz-proto/examples/0.7.2/no_forks" \
  --target-sock /tmp/tessera-sock/jam_target.sock
```

```bash
python3 ../tessera-doom/test-suites/ext/jam-conformance/fuzz-proto/minifuzz/minifuzz.py \
  -d "/home/darkknight/Chainscore Labs/Tesseract/tessera-doom/test-suites/ext/jam-conformance/fuzz-proto/examples/0.7.2/forks" \
  --target-sock /tmp/tessera-sock/jam_target.sock
```

### How the release image is expected to run in conformance tooling

Equivalent raw command shape for the published image:

```bash
docker run --rm \
  -e JAM_FUZZ=1 \
  -e JAM_FUZZ_SPEC=tiny \
  -e JAM_FUZZ_DATA_PATH=/data \
  -e JAM_FUZZ_SOCK_PATH=/sock/jam_target.sock \
  -e JAM_FUZZ_LOG_LEVEL=info \
  -v /tmp/tessera-data:/data \
  -v /tmp/tessera-sock:/sock \
  ghcr.io/chainscore/tessera:v0.7.2
```

The web-app/runner will do the same kind of lifecycle automatically:

- pull the image
- start the container with `JAM_FUZZ_*`
- wait for the socket
- run the fuzzer against that socket
- stop the container

Docker-based binary test harness:

```bash
./test-binary.sh build
./test-binary.sh test storage
./test-binary.sh test refine
```

## Core Pytest Commands

### Main repo tests

```bash
uv run pytest tests/
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest tests/benchmark
```

Common focused runs:

```bash
uv run pytest tests/unit/safrole
uv run pytest tests/unit/execution
uv run pytest tests/unit/state
uv run pytest tests/unit/api
uv run pytest tests/integration/genesis
uv run pytest tests/integration/jamnp
uv run pytest tests/integration/pj
```

With coverage:

```bash
uv run pytest --cov=jam --cov-report=html tests/
```

### Test layout currently present

- `tests/unit`: `api`, `audit`, `consensus`, `disputes`, `erasure_coding`, `execution`, `genesis`, `incore`, `merkle`, `mmr`, `safrole`, `state`, `traces`, `trie`, `types`
- `tests/integration`: `genesis`, `jamnp`, `pj`, `traces`
- `tests/benchmark`

## W3F STF Harness

Primary STF runner:

```bash
uv run pytest test-suites/harness/w3f/stf/test_w3f_vectors.py -q --no-rpc
```

Filter by module, spec, or pattern:

```bash
uv run pytest test-suites/harness/w3f/stf/test_w3f_vectors.py --module safrole --spec tiny --pattern "*.json" -s -vv --no-rpc
uv run pytest test-suites/harness/w3f/stf/test_w3f_vectors.py --module accumulate --spec tiny --pattern "*.json" -s -vv --no-rpc
uv run pytest test-suites/harness/w3f/stf/test_w3f_vectors.py --module reports --spec full --pattern "*.json" -q --no-rpc
uv run pytest test-suites/harness/w3f/stf/test_w3f_vectors.py --module reports --pattern "anchor_not_recent-1.json" -s -vv --no-rpc
```

Current W3F STF modules in this repo:

- `accumulate`
- `assurances`
- `authorizations`
- `disputes`
- `history`
- `preimages`
- `reports`
- `safrole`
- `statistics`

Convenience wrapper for all tiny STF modules:

```bash
./scripts/run-stf-tiny-verbose.sh
SPEC=tiny PATTERN="*.json" JAM_LOG_LEVEL=debug ./scripts/run-stf-tiny-verbose.sh
```

## W3F Trace Harness

Unified trace runner:

```bash
uv run pytest test-suites/harness/w3f/traces/test_traces_unified.py -q --no-rpc
uv run pytest test-suites/harness/w3f/traces/test_traces_unified.py --module "*" --pattern "*00000176.bin" -s --no-rpc
uv run pytest test-suites/harness/w3f/traces/test_traces_unified.py --module "*6948" --pattern "*296.bin" -s --no-rpc
```

Other trace harness variants present:

```bash
uv run pytest test-suites/harness/w3f/traces/test_traces.py
uv run pytest test-suites/harness/w3f/traces/test_traces_linear.py
uv run pytest test-suites/harness/w3f/traces/test_traces_linear_unified.py
uv run pytest test-suites/harness/w3f/traces/test_traces_conf.py
uv run pytest test-suites/harness/w3f/traces/test_decode_traces.py
```

Repo wrapper script:

```bash
./scripts/tests.sh traces --module safrole --pattern "*.bin"
./scripts/tests.sh traces-linear --module safrole --pattern "*.bin"
```

## Other Harnesses

### Jamduna STF

```bash
uv run pytest test-suites/harness/jamduna/stf/test_jamduna_vectors.py -q
uv run pytest test-suites/harness/jamduna/stf/test_jamduna_vectors.py --module assurances --pattern "*.json"
uv run pytest test-suites/harness/jamduna/stf/test_jamduna_vectors.py --module accumulate --pattern "*.json"
```

### W3F codec, trie, shuffle, PVM

```bash
uv run pytest test-suites/harness/w3f/test_codec.py
uv run pytest test-suites/harness/w3f/test_trie.py
uv run pytest test-suites/harness/w3f/test_shuffle.py
uv run pytest test-suites/harness/w3f/pvm/test_pvm.py
```

## Perf And Benchmark Commands

### Repo-local benchmark tests

```bash
uv run pytest tests/benchmark
uv run pytest tests/unit/erasure_coding/benchmark_erasure_coding.py -s
```

### Perf harness

```bash
uv run pytest test-suites/perf/tests/test_block_import.py -s
uv run pytest test-suites/perf/tests/test_transition_w_pvm.py -s
```

### Standalone benchmark utility

`tests/benchmark/wp_bench.py` defines `wp_bench()` but is not wired to a CLI. Run it from a short Python snippet if needed:

```bash
uv run python -c "from tests.benchmark.wp_bench import wp_bench; wp_bench()"
```

## Fuzzing And Trace Replay

### Minifuzz helper

```bash
uv run python scripts/run_minifuzz.py --help
uv run python scripts/run_minifuzz.py --tessera . --mode both --socket /tmp/jam_target.sock -y
uv run python scripts/run_minifuzz.py --tessera . --mode no_forks -y
```

### Parallel trace runner

```bash
uv run python scripts/run_traces_parallel.py --help
uv run python scripts/run_traces_parallel.py --module "*6948" --pattern "*296.bin" -j 8 --no-rpc
uv run python scripts/run_traces_parallel.py --module "*" --pattern "*.bin" -j 16 --no-rpc
```

Notes:

- `genesis.bin`, `genesis.json`, and `00000000.json` are skipped automatically.
- `-j` is the worker count. Start with `6` to `8` if you still want the machine responsive.

### Raw trace replay helper

```bash
uv run python tests/integration/traces/fuzz.py \
  --trace-dir test-suites/ext/jam-conformance/fuzz-reports/0.7.2/traces \
  --module "*" \
  --pattern "*.bin" \
  --target-sock /tmp/jam_target.sock
```

## Local Network Helpers

### Pure Tessera local network

```bash
uv run python run_local_net.py
./scripts/testnet_sync.sh 6
./scripts/testnet-tmux.sh 6
./scripts/tsr_testnet.sh
```

### Mixed Tessera + PolkaJam tmux network

```bash
./scripts/testnet.sh /path/to/polkajam
```

## Playground Scripts

These live under `test-suites/playground/scripts` and assume the playground toolchain is installed.

```bash
./test-suites/playground/scripts/start-testnet.sh
./test-suites/playground/scripts/stop-testnet.sh
./test-suites/playground/scripts/build-services.sh <service-name>
./test-suites/playground/scripts/deploy-services.sh
```

## Test Suite Maintenance

```bash
./test-suites/scripts/update_vectors.sh
git submodule update --init --recursive
```

## Azure Deployment

```bash
./scripts/deploy-testnet.sh
./scripts/deploy-testnet.sh telemetry-host:port
```

## Known Mismatches And Stale Bits

- `uv run jam` and `uv run python jam/cli.py` are different CLIs. Use the one that matches your workflow.
- The root `README.md` includes CLI examples that match `uv run jam`, not `jam/cli.py`.
- `scripts/tests.sh` currently uses `poetry run`, while the repo otherwise uses `uv`.
- `pyproject.toml` defines `uv run poe tests = ./scripts/test.sh`, but the file present in this repo is `scripts/tests.sh`.
- `pyproject.toml` defines `deploy-azure = ./scripts/deploy-to-azure.sh`, but the script present in this repo is `scripts/deploy-testnet.sh`.

## Useful Discovery Commands

```bash
rg --files tests test-suites/harness scripts
find tests -maxdepth 2 -type d | sort
find test-suites/harness -maxdepth 3 -type d | sort
```
