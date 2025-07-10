import pytest
import asyncio
import signal
import shutil

from multiprocessing import Process

import logging
import os
import time

from dotenv import load_dotenv
from tsrkit_types import U32, TypedVector, U64, Dictionary, Bool
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U16, U8, Uint

from jam.logging import setup_logging
from jam.network.base.certificate import generate_san
from jam.types import WorkReport, WorkPackage, Authorizer, RefineContext, ImportSpec, ExtrinsicSpec, WorkItem, \
    OpaqueHash, WorkPackageSpec, WorkResult, WorkExecResult, WorkReportHash, Hash, HeaderHash, StateRoot, BeefyRoot, \
    WorkPackageHash, ErasureRoot, ExportsRoot
from jam.types.work import RefineLoad
from jam.utils.chainspec import chain_config

from jam.consensus.grandpa.finality import Finality
from jam.settings import setup_setting

from jam.network.peer import Peer
from jam.network.node import Node

from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state, State
from jam.types.protocol.crypto import BlsPublic
from jam.types.block import Block
from jam.types.protocol.validators import (
    IPAddress,
    ValidatorData,
    ValidatorMetadata,
)

from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, SLOT_PERIOD
from jam.types.work.manifest import Extrinsics
from jam.logging import get_logger
from jam.network.protocols.ce_133 import WorkPackageSubmission, CE133Data, OptBool
from jam.network.protocols.ce_133 import WorkPackageCore
from jam.types.protocol.core import CoreIndex
from jam.work_package.processor import Processor
from jam.work_package.stores.reports import ReportsDA
from tests.integration.jamnp.utils.run_node import run_node_process

CLIENTS = [
    {
        "port": 40000,
        "role": "VALIDATOR",
        "theme": "matrix",
        "genesis": True
    },
    {
        "port": 40001,
        "role": "VALIDATOR",
        "theme": "default",
        "genesis": True
    },
    {
        "port": 40006,
        "role": "BUILDER",
        "theme": "polkadot",
        "genesis": True
    },
]

# Logger for WP Production
logger = get_logger("in_core")

wp = WorkPackage(authorization=Bytes(b'\x01'), auth_code_host=U32(42), authorizer=Authorizer(code_hash=OpaqueHash(b'\x10S&j\x87\x96\xf3\xfb\xb2\x93b3\xf7\xb0"\x18iK\x04\xe8`J\xc3\xc8\x89.AT)\xf0\xa1-'), params=Bytes(b'\x9a\xb5\xae\xec\xe7y0\xccP\x17')), context=RefineContext(anchor=HeaderHash(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), state_root=StateRoot(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), beefy_root=BeefyRoot(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), lookup_anchor=HeaderHash(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), lookup_anchor_slot=U32(0), prerequisites=TypedVector[OpaqueHash]([])), items=TypedVector[WorkItem]([WorkItem(service=U32(1), code_hash=OpaqueHash(b's\x8b\x9a\xff:\xcb\xcc\xabvnE\xcaN\xe1\x1d\x1d\xb9c\xca\xd1|\x9b\x931\xb2\xdaK\x10\xba@\xa8\x94'), payload=Bytes(b'bobaboba'), refine_gas_limit=U64(1000), accumulate_gas_limit=U64(1000), import_segments=TypedVector[ImportSpec]([]), extrinsic=TypedVector[ExtrinsicSpec]([]), export_count=U16(1))]))
wr = WorkReport(package_spec=WorkPackageSpec(hash=WorkPackageHash(b'}\xc8\xf4d\xb3\x1fH\xa0\xe4\x9c\x1f\x96\x86\xfd\xcb\x13\xd8\xde\xee%c\xee!d\xac\x88\xefg\x8b\xdd\xf7G'), length=U32(253), erasure_root=ErasureRoot(b'4k;3U19\xea0\xf9YC\xe86\x0c\xa2\xd4p\xefmf\xfb\xa9\x03\xcb`\xefl\xd4M\xaf\x02'), exports_root=ExportsRoot(b'<\xf9\xb7\xc0\x11\xa5,\xcd[%\x13\xc6\x8c\xde#\xeb\xa2\x07Hst\xb0tt-\xa4\x13\xd9\x05&;\x91'), exports_count=U16(1)), context=RefineContext(anchor=HeaderHash(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), state_root=StateRoot(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), beefy_root=BeefyRoot(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), lookup_anchor=HeaderHash(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), lookup_anchor_slot=U32(0), prerequisites=TypedVector[OpaqueHash]([])), core_index=Uint(1), authorizer_hash=b'\x9e\xcc\x01*<\xc8\xbbzG}\xef(\xac\xfd\xb6\xe5\xb0Y\xd7\xccU9y\x98\x95,\xefY\xa9\x1a\x18\x86', auth_output=b'\x01', segment_root_lookup=Dictionary({}), results=TypedVector[WorkResult]([WorkResult(service_id=U32(1), code_hash=b's\x8b\x9a\xff:\xcb\xcc\xabvnE\xcaN\xe1\x1d\x1d\xb9c\xca\xd1|\x9b\x931\xb2\xdaK\x10\xba@\xa8\x94', payload_hash=b'\xad\x83\xe1\x97-\xd0\xa6\x04\xeb\xe9\x85|\xad\xf9\x0f\x9a\x96\xc3,\xf4|{\x82\xc8\x04\xfb\xe8=\x0e\xaa\xf0\xaf', accumulate_gas=U64(1000), result=WorkExecResult(b''), refine_load=RefineLoad(gas_used=Uint(49), imports=Uint(0), extrinsic_count=Uint(0), extrinsic_size=Uint(0), exports=Uint(1)))]), auth_gas_used=Uint(7))
wr_hash = WorkReportHash(b'\x18is\xa2\xd8\x8e\x15\xbd5H\xc6\xd3\xe3\xed\x87\xd6?s\xae\x1aT\xe8\x04\x9eQ\xea\xdc\xcd\x9e\x88\xfcs')
wc = WorkPackageCore(wp, CoreIndex(1))
ext = Extrinsics([])

async def node_tasks(node: Node):
    """Define Node tasks"""

    # Wait for node to initialize
    await asyncio.sleep(5)
    print("NODE STARTED")

    if node.is_builder:
        protocol = WorkPackageSubmission()


        package_len = Uint[32](len(wc.encode()))
        ext_len = Uint[32](len(ext.encode()))
        data = CE133Data(package_len=package_len, package_data=wc, extrinsics_len=ext_len, extrinsics=ext)

        responses = await protocol.transmit(node, data)

        # expected_message = Bool(True)

        for response in responses:
            # print("resp", response)
            assert response.unwrap()._value == True
            print("BUILDER ASSERTION SUCCESS")


    else:
        # Wait for refinement to happen
        await asyncio.sleep(20)
        from jam.settings import settings

        # Check if report exists in db or not
        try:
            db = settings.d3l
            da = ReportsDA(db)

            rep = da.get(wr_hash)
            assert rep == wr
            print("WR ASSERTION SUCCESS")

        except Exception as e:
            raise AssertionError("Report not found on Guarantor")


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
            args=("", env_path, client["genesis"], client["theme"], is_builder, is_validator, node_tasks)
        )
        processes.append(p)

    print("STARTING PROCESSES...")
    for p in processes:
        p.start()

    print("ALL PROCESSES STARTED")

    # KEEP TEST ALIVE FOR SOME TIME
    await asyncio.sleep(20)

    print("TERMINATING PROCESSES")
    for p in processes:
        p.terminate()
    for p in processes:
        p.join()

    print("END OF TEST")

