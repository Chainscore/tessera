import os

from concurrent.futures.process import ProcessPoolExecutor
from .worker import Worker

MAX_WORKERS = min(16, os.cpu_count())
EXECUTOR: ProcessPoolExecutor | None = None
PUBKEYS: list[bytes] | None = None

def setup_executor(pubkeys: list[bytes]):
    global EXECUTOR, PUBKEYS

    if pubkeys == PUBKEYS:
        return

    if EXECUTOR:
        shutdown_executor()

    # multiprocessing.set_start_method("spawn", force=False)
    PUBKEYS = pubkeys

    EXECUTOR = ProcessPoolExecutor(
        max_workers=MAX_WORKERS,
        initializer=Worker.init_worker,
        initargs=(pubkeys,),
    )

def get_executor():
    global EXECUTOR

    if not EXECUTOR:
        raise ValueError("Executor not setup!")

    return EXECUTOR

def shutdown_executor():
    global EXECUTOR

    try:
        EXECUTOR.shutdown(wait=True)
    except Exception:
        raise
    finally:
        EXECUTOR = None

def get_curr_keys():
    global PUBKEYS

    return PUBKEYS