import os
import asyncio
import shutil
from multiprocessing import Process
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from jam.utils.benchmark import write_json
from .run_node import run_node_process
from .run_polkajam import run_polkajam


class Role(Enum):
    VAL = 0
    BUILDER = 1
    PJAM = 3


@dataclass
class Client:
    role: Role
    # Port in case of validator/builder, else validator index
    idx: int
    theme: str = "default"
    genesis = True

async def setup_processes(clients: list[Client], node_tasks: list[Optional[Callable]], max_time = 20, rpc_flag: bool = True):
    processes = []

    for client in clients:
        if client.role == Role.PJAM:
            p = Process(
                target=run_polkajam,
                args=("", client.idx)
            )
        else:
            env_path = f"envs/{client.idx}.env"
            is_validator = client.role == Role.VAL
            is_builder = client.role == Role.BUILDER

            dir_path = f"/data/{client.idx}"

            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                print(f"REMOVED DIR: {dir_path}")

            p = Process(
                target=run_node_process,
                args=(
                    "data/tmp",
                    env_path,
                    client.genesis,
                    client.theme,
                    is_builder,
                    is_validator,
                    node_tasks,
                    rpc_flag
                ),
            )
        processes.append(p)

    print("STARTING PROCESSES...")
    for p in processes:
        p.start()

    print("ALL PROCESSES STARTED")

    # KEEP TEST ALIVE FOR SOME TIME
    await asyncio.sleep(max_time)

    print("TERMINATING PROCESSES")
    for p in processes:
        p.terminate()
    for p in processes:
        p.join()


    print("END OF TEST")

