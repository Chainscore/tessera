import pytest
import asyncio
import signal
import shutil

from multiprocessing import Process

import logging
import os
import time

from dotenv import load_dotenv
from jam.operations.operator import operate
from tsrkit_types import U32, TypedVector, U64, Dictionary
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U16, Uint
from jam.network.start import start_node as start_global_node

from jam.log_setup import setup_logging
from jam.network.base.certificate import generate_san
from jam.types import (
    WorkReport,
    WorkPackage,
    Authorizer,
    RefineContext,
    ImportSpec,
    ExtrinsicSpec,
    WorkItem,
    OpaqueHash,
    WorkPackageSpec,
    WorkResult,
    WorkExecResult,
    WorkReportHash,
    HeaderHash,
    StateRoot,
    BeefyRoot,
    WorkPackageHash,
    ErasureRoot,
    ExportsRoot,
)
from jam.types.work import RefineLoad
from jam.utils.chainspec import chain_config

from jam.finality.finality import Finality
from jam.settings import setup_setting

# from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state
from jam.block import Block

from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, SLOT_PERIOD
from jam.types.work.manifest import Extrinsics
from jam.log_setup import node_logger as logger
from jam.network.protocols.ce_133 import WorkPackageSubmission, CE133Data
from jam.network.protocols.ce_133 import WorkPackageCore
from jam.types.protocol.core import CoreIndex

CLIENTS = [
    {"port": 40000, "role": "VALIDATOR", "theme": "matrix", "genesis": True},
    {"port": 40001, "role": "VALIDATOR", "theme": "default", "genesis": True},
    {"port": 40002, "role": "VALIDATOR", "theme": "default", "genesis": True},
    {"port": 40003, "role": "VALIDATOR", "theme": "default", "genesis": True},
    {"port": 40004, "role": "VALIDATOR", "theme": "default", "genesis": True},
    {"port": 40005, "role": "VALIDATOR", "theme": "default", "genesis": True},
    {"port": 40006, "role": "BUILDER", "theme": "polkadot", "genesis": True},
]

wp = WorkPackage(
    authorization=Bytes(b"\x01"),
    auth_code_host=U32(42),
    authorizer=Authorizer(
        code_hash=OpaqueHash(
            b'\x10S&j\x87\x96\xf3\xfb\xb2\x93b3\xf7\xb0"\x18iK\x04\xe8`J\xc3\xc8\x89.AT)\xf0\xa1-'
        ),
        params=Bytes(b"\x9a\xb5\xae\xec\xe7y0\xccP\x17"),
    ),
    context=RefineContext(
        anchor=HeaderHash(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        state_root=StateRoot(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        beefy_root=BeefyRoot(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        lookup_anchor=HeaderHash(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        lookup_anchor_slot=U32(0),
        prerequisites=TypedVector[OpaqueHash]([]),
    ),
    items=TypedVector[WorkItem](
        [
            WorkItem(
                service=U32(1),
                code_hash=OpaqueHash(
                    b"s\x8b\x9a\xff:\xcb\xcc\xabvnE\xcaN\xe1\x1d\x1d\xb9c\xca\xd1|\x9b\x931\xb2\xdaK\x10\xba@\xa8\x94"
                ),
                payload=Bytes(b"bobaboba"),
                refine_gas_limit=U64(1000),
                accumulate_gas_limit=U64(1000),
                import_segments=TypedVector[ImportSpec]([]),
                extrinsic=TypedVector[ExtrinsicSpec]([]),
                export_count=U16(1),
            )
        ]
    ),
)
wr = WorkReport(
    package_spec=WorkPackageSpec(
        hash=WorkPackageHash(
            b"}\xc8\xf4d\xb3\x1fH\xa0\xe4\x9c\x1f\x96\x86\xfd\xcb\x13\xd8\xde\xee%c\xee!d\xac\x88\xefg\x8b\xdd\xf7G"
        ),
        length=U32(253),
        erasure_root=ErasureRoot(
            b"4k;3U19\xea0\xf9YC\xe86\x0c\xa2\xd4p\xefmf\xfb\xa9\x03\xcb`\xefl\xd4M\xaf\x02"
        ),
        exports_root=ExportsRoot(
            b"<\xf9\xb7\xc0\x11\xa5,\xcd[%\x13\xc6\x8c\xde#\xeb\xa2\x07Hst\xb0tt-\xa4\x13\xd9\x05&;\x91"
        ),
        exports_count=U16(1),
    ),
    context=RefineContext(
        anchor=HeaderHash(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        state_root=StateRoot(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        beefy_root=BeefyRoot(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        lookup_anchor=HeaderHash(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
        lookup_anchor_slot=U32(0),
        prerequisites=TypedVector[OpaqueHash]([]),
    ),
    core_index=Uint(1),
    authorizer_hash=b"\x9e\xcc\x01*<\xc8\xbbzG}\xef(\xac\xfd\xb6\xe5\xb0Y\xd7\xccU9y\x98\x95,\xefY\xa9\x1a\x18\x86",
    auth_output=b"\x01",
    segment_root_lookup=Dictionary({}),
    results=TypedVector[WorkResult](
        [
            WorkResult(
                service_id=U32(1),
                code_hash=b"s\x8b\x9a\xff:\xcb\xcc\xabvnE\xcaN\xe1\x1d\x1d\xb9c\xca\xd1|\x9b\x931\xb2\xdaK\x10\xba@\xa8\x94",
                payload_hash=b"\xad\x83\xe1\x97-\xd0\xa6\x04\xeb\xe9\x85|\xad\xf9\x0f\x9a\x96\xc3,\xf4|{\x82\xc8\x04\xfb\xe8=\x0e\xaa\xf0\xaf",
                accumulate_gas=U64(1000),
                result=WorkExecResult(b""),
                refine_load=RefineLoad(
                    gas_used=Uint(49),
                    imports=Uint(0),
                    extrinsic_count=Uint(0),
                    extrinsic_size=Uint(0),
                    exports=Uint(1),
                ),
            )
        ]
    ),
    auth_gas_used=Uint(7),
)
wr_hash = WorkReportHash(
    b"\x18is\xa2\xd8\x8e\x15\xbd5H\xc6\xd3\xe3\xed\x87\xd6?s\xae\x1aT\xe8\x04\x9eQ\xea\xdc\xcd\x9e\x88\xfcs"
)
wc = WorkPackageCore(wp, CoreIndex(1))
ext = Extrinsics([])


async def start_node():
    """Define Node tasks"""
    from jam.network.start import node
    # Wait for node to initialize
    await asyncio.sleep(2)
    print("NODE STARTED", ": Builder" if node.is_builder else "node")

    if node.is_builder:
        # processor = Processor(node)
        # expected_wr, expected_wr_hash = processor.process(wp, CoreIndex(1), ext)
        # assert expected_wr == wr and expected_wr_hash == wr_hash

        protocol = WorkPackageSubmission()

        package_len = Uint[32](len(wc.encode()))
        ext_len = Uint[32](len(ext.encode()))
        data = CE133Data(
            package_len=package_len, package_data=wc, extrinsics_len=ext_len, extrinsics=ext
        )

        responses = await protocol.transmit(data)

        # expected_message = Bool(True)

        for response in responses:
            # print("resp", response)
            assert response.unwrap()._value == True
            print("BUILDER ASSERTION SUCCESS")


def run_node_process(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
):
    # Handle clean termination
    def handle_sigterm(signum, frame):
        exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    asyncio.run(run_node(genesis_path, env, start_genesis, theme, is_builder, is_validator))


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_connection():
    print("START OF TEST")

    processes = []

    for client in CLIENTS:
        env_path = f"envs/{client['port']}.env"
        is_validator = client["role"] == "VALIDATOR"
        is_builder = client["role"] == "BUILDER"

        dir_path = f"/data/{client['port']}"

        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"REMOVED DIR: {dir_path}")

        p = Process(
            target=run_node_process,
            args=("", env_path, client["genesis"], client["theme"], is_builder, is_validator),
        )
        processes.append(p)

    print("STARTING PROCESSES...")
    for p in processes:
        p.start()

    print("ALL PROCESSES STARTED")

    # KEEP TEST ALIVE FOR SOME TIME
    await asyncio.sleep(36)

    print("TERMINATING PROCESSES")
    for p in processes:
        p.terminate()
    for p in processes:
        p.join()

    print("END OF TEST")


async def run_node(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
):
    """Main fn to start the node"""
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS  # Actual Genesis time for JAM Common Era
    init_ts = int((time.time() - genesis_ts) / SLOT_PERIOD)
    init_ep = int(init_ts // EPOCH_LENGTH)

    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env, override=True)

    name = os.environ["NODE_NAME"]
    port = os.environ["PORT"]
    seed = os.environ["SEED"]
    host = os.environ["HOST"]

    if not name or not port or not host or not seed:
        raise ValueError(f"Missing node info in {env}")

    # ---------- SETUP LOGGING ----------
    environment = os.environ.get("ENVIRONMENT", "development")
    log_level = os.environ.get("LOG_LEVEL", None)

    setup_logging(
        theme=theme,
        node_name=name,
        environment=environment,
        min_level=getattr(logging, log_level.upper()) if log_level else None,
    )

    # ---------- SETUP SETTINGS ----------
    settings = setup_setting(name=name, port=int(port), seed=int(seed), data_path="data/")

    main_db = settings.main_db

    logger.info(
        "Starting JAM node",
        name=name,
        port=port,
        ts=init_ts,
        epoch=init_ep,
        spec=chain_config.name,
        environment=environment,
        is_builder=is_builder,
        is_validator=is_validator,
    )

    try:
        # Set genesis state
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, "dev-spec.json")
        state.store.disable_cache()
        # # update_state(state)

        settings.update()

        block = Block.genesis()
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db, True)

        settings.update()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(start_global_node(host, int(port)))
            tg.create_task(operate(is_builder))
            # tg.create_task(start_node(tsr_node))

    except KeyboardInterrupt:
        logger.info(
            "JAM node shutting down gracefully",
            node_name=name,
            port=port,
            reason="keyboard_interrupt",
        )
    except Exception as e:
        logger.critical(
            "JAM node fatal error",
            node_name=name,
            port=port,
            error=str(e)[:200],
            error_type=type(e).__name__,
        )

        # Close db connections
        settings.clear()

        raise
