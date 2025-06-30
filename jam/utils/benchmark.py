from time import perf_counter as now
from contextlib import contextmanager

from jam.logging import get_logger

# Module-specific logger
logger = get_logger("in_core")

BENCHMARK_FILE = "benchmark_results.txt"

benchmark_results = []

@contextmanager
def benchmark(label: str):
    start = now()
    yield
    duration = now() - start
    slot_fraction = 6 / duration if duration > 0 else float('inf')

    logger.debug(f"{label} in {duration:.6f} seconds (~ 1/{int(slot_fraction)} of a slot)")

    benchmark_results.append({
        "label": label,
        "duration_sec": duration,
        "slot_fraction": slot_fraction
    })

def write_benchmarks_to_txt(filename=BENCHMARK_FILE):
    global benchmark_results
    label_width = 30
    time_width = 12
    fraction_width = 15

    if not benchmark_results:
        logger.debug("No new benchmark results to write.")
        return

    with open(filename, "a") as f:
        # If file empty or first write, write header
        if f.tell() == 0:
            f.write(f"{'Label':{label_width}} | {'Time (s)':>{time_width}} | {'Slot Fraction':>{fraction_width}}\n")
            f.write("-" * (label_width + time_width + fraction_width + 7) + "\n")

        for r in benchmark_results:
            f.write(f"{r['label']:{label_width}} | {r['duration_sec']:>{time_width}.6f} | {r['slot_fraction']:>{fraction_width}.2f}\n")
        # Write dashed line after this batch
        f.write("-" * (label_width + time_width + fraction_width + 7) + "\n")

    benchmark_results = []

