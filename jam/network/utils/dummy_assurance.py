import asyncio
from math import floor

from sympy.physics.units import current

from jam.storage.db.kv import KVStore
from jam.state.state import State
from jam.types.protocol.crypto import Ed25519Signature
from jam.types.extrinsics.assurances import AvailBitField
from jam.types.work.package import OpaqueHash
from jam.utils.constants import EPOCH_LENGTH

from tests.dummy.utils import create_dummy_bytes32, create_dummy_bytes64, create_dummy_bytes
from jam.types.extrinsics.assurances import Assurance
from jam.network.node import Node
from time import time
from jam.network.protocols.ce_141 import AssuranceDistribution, CE141Data
from jam.config.logging import logger


def create_dummy_assurances() -> Assurance:
    return Assurance (
        header_hash=OpaqueHash(create_dummy_bytes32()) ,
        bitfield=AvailBitField("0x01"),
        ed25519_signature=Ed25519Signature(create_dummy_bytes(64))
    )

async def assurance_distribution(node : Node):
    """ """
    # Record genesis timestamp in second
    genesis_ts = time()
    assurance_send = AssuranceDistribution()

    assurance_iter = 0
    while True:
        if not node.is_initialized:
            logger.info(f"🔄 ({node.name}) Network is not initialized, skipping assurance")
            await asyncio.sleep(6)
            genesis_ts = time()
            continue

        # state = State.load(db)
        current_timeslot = (time() - genesis_ts) // 6
        ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)


        print("dhokha", node)
        if node.is_validator:
            print("inside the protocol 141")
            assurances = create_dummy_assurances()
            assurance_data : CE141Data = CE141Data(assurances)

            print("assurance_data", assurance_data)
            await assurance_send.transmit(node, assurance_data)
        else:
            print("skipping in assurance")
            logger.info(f"🔄 ({node.name}) skipping Node")

        await asyncio.sleep(6 - (time() - genesis_ts) % 6)
        assurance_iter += 1