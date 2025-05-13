import asyncio
import json
import os

from jam.config.logging import setup_logging, logger
from jam.chainspec import chain_config
from jam.config.settings import settings
from jam.db.kv import KVStore

from jam.network.peer import Peer
from jam.network.node import Node
from jam.network.utils.dummy_wpb import wp_producer
from jam.network.utils.dummy_segment_shard import segment_shard_request

from jam.consensus.bp_engine import BlockProducer
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint
from jam.state.state import State
from jam.types.base.integers.fixed import U16, U8
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic
from jam.types.block import Block
from jam.types.header import Header
from jam.types.protocol.validators import (
    IPAddress,
    ValidatorData,
    ValidatorMetadata,
    ValidatorName,
    ValidatorsData,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


async def main(
    name: str,
    genesis_path: str,
    port: int,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
) -> None:
    # Setup logging
    setup_logging(theme=theme, node_name=name)

    logger.info(
        f"Starting {name} node",
        spec=chain_config.name,
        listen_port=port,
    )
    try:
        # Initialize components
        genesis = json.load(open(genesis_path))
        peerlist = genesis["peers"]
        peers = [
            Peer(
                port=pr["metadata"]["port"],
                host=".".join([str(val) for val in pr["metadata"]["host"]]),
                san=pr["id"],
            )
            for pr in peerlist
        ]

        # Load validator data from seeds
        my_keys = json.load(open("seeds/keys.json"))[str(port)]
        ed25519_public = Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(my_keys["ed25519_private"][2:])
        ).public_key()

        bandersnatch_public = BandersnatchPublic(
            (
                BandersnatchPoint.generator_point()
                * int.from_bytes(
                    bytes.fromhex(my_keys["bandersnatch_private"][2:]), "little"
                )
            )
            .point_to_string()
            .hex()
        )
        my_data = ValidatorData(
            bandersnatch_public,
            ed25519_public,
            BlsPublic(bytes(144)),
            ValidatorMetadata(
                name=ValidatorName(name),
                host=IPAddress([U8(127), U8(0), U8(0), U8(1)]),
                port=U16(port),
            ),
        )

        tsr_node = Node(
            node_name=name,
            node_id=str(port),
            host="127.0.0.1",
            port=port,
            peers=peers,
            validator_data=my_data,
            is_builder=is_builder,
            is_validator=is_validator,
        )

        settings.NODE_NAME = name
        settings.LISTEN_PORT = port
        settings.NODE_PATH = f"db/{port}"
        settings.DB_PATH = f"{settings.NODE_PATH}/node"
        settings.D3L_PATH = f"{settings.NODE_PATH}/d3l"

        os.makedirs(settings.DB_PATH, exist_ok=True)
        os.makedirs(settings.D3L_PATH, exist_ok=True)

        logger.info(f"Node Running on port: {settings.LISTEN_PORT}. Dbs: {settings.DB_PATH} {settings.D3L_PATH}")
        db = KVStore(settings.DB_PATH)

        if start_genesis:
            # Start from genesis
            genesis_vals = ValidatorsData.from_json(peerlist)

            block = Block.from_random(0)
            block.header = Header.from_json(genesis["header"])
            block.save(db)

            state = State.genesis()
            state.save(db)

            block_producer = BlockProducer(tsr_node, db)

            async with asyncio.TaskGroup() as tg:
                tg.create_task(tsr_node.initialize())
                if tsr_node.is_builder:
                    tg.create_task(wp_producer(tsr_node, db))
                else:
                    tg.create_task(segment_shard_request(tsr_node, db))
                    # tg.create_task(block_producer.run())


        else:
            # TODO: Sync from peers
            raise NotImplementedError("Syncing from peers is not implemented yet")

    except KeyboardInterrupt:
        logger.info(f"👋 ({name}) Shutting down JAM node 🔐")
    except Exception as e:
        logger.exception(f"💥 ({name}) Fatal error", error=str(e)[:100])
        raise
