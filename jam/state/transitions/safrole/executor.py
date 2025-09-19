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

    if EXECUTOR:
        shutdown_executor()

    # TODO: If required, move this to setup_state()
    # NOTE: fork isnt safe when parent processes are multithreaded
    # By default Linux systems have fork which is faster, but Windows and IoS systems have spawn, which is slower.

    # multiprocessing.set_start_method("fork", force=False)

    PUBKEYS = pubkeys

    EXECUTOR = ProcessPoolExecutor(
        max_workers=min(MAX_TICKETS_PER_EXTRINSIC, os.cpu_count()),
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