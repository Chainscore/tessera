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
