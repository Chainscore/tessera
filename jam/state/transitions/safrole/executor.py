import multiprocessing
import os

from concurrent.futures.process import ProcessPoolExecutor

from jam.utils.constants import MAX_TICKETS_PER_EXTRINSIC
from .worker import Worker

EXECUTOR: ProcessPoolExecutor | None = None
PUBKEYS: list[bytes] | None = None

def setup_executor(pubkeys: list[bytes]):
    global EXECUTOR, PUBKEYS

    if pubkeys == PUBKEYS:
        return

    max_workers = min(MAX_TICKETS_PER_EXTRINSIC, os.cpu_count())

    if EXECUTOR:
        shutdown_executor()

    PUBKEYS = pubkeys

    EXECUTOR = ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=Worker.init_worker,
        initargs=(pubkeys,),
    )

def get_executor():
    global EXECUTOR

    if not EXECUTOR:
        raise ValueError("Executor not setup!")

    return EXECUTOR

def shutdown_executor(wait: bool = False):
    global EXECUTOR

    if not EXECUTOR:
        print("No Executor to shutdown!")
        return

    try:
        EXECUTOR.shutdown(wait=wait)
    except Exception:
        raise
    finally:
        EXECUTOR = None

def get_curr_keys():
    global PUBKEYS

    return PUBKEYS