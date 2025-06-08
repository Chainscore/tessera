import asyncio
import json
import os

from dotenv import load_dotenv
from tsrkit_types.bytes import Bytes

from jam.config.keys import setup_keys
from jam.config.logging import setup_logging, logger
from jam.config.chainspec import chain_config
from rockstore import RockStore
from jam.network.peer import Peer
from jam.network.node import Node
from jam.network.utils.dummy_wpb import wp_producer
from jam.consensus.bp_engine import BlockProducer
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint
from jam.state.state import setup_state
from tsrkit_types.integers import U16, U8, Uint, U32
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Hash
from jam.types.block import Block, Header
from jam.types.protocol.validators import (
    IPAddress,
    ValidatorData,
    ValidatorMetadata,
)



async def main(
    genesis_path: str,
    db_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
) -> None:
    load_dotenv(env)

    name = os.environ["NODE_NAME"]
    port = os.environ["PORT"]
    seed = os.environ["SEED"]

    if not name or not port:
        raise ValueError(f"Name or Port not found in {env}")

    # Setup logging
    setup_logging(theme=theme, node_name=name)

    logger.info(
        f"Starting {name} node on {port}",
        spec=chain_config.name,
        listen_port=port,
    )
    try:
        if not start_genesis:
            # TODO: Sync from peers
            raise NotImplementedError("Syncing from peers is not implemented yet")

        # Initialize components
        dev_spec = json.load(open(genesis_path))

        # Set genesis state
        db = RockStore(db_path)
        state = setup_state(db, "dev-spec.json")
        keys = setup_keys(int(os.environ["SEED"]))

        peers = [
            Peer(
                port=int(val.metadata.port),
                host=".".join([str(int(val)) for val in val.metadata.host]),
                san=val.metadata.name,
            )
            for val in state.kappa
        ]

        my_data = ValidatorData(
            keys.bandersnatch_public,
            keys.ed25519_public,
            BlsPublic(bytes(144)),
            ValidatorMetadata(
                name=Bytes[10](bytes(10)),
                protocol=Uint[16](2 ** 16 - 1),
                host=IPAddress([U8(0), U8(0), U8(0), U8(0)]),
                port=U16(port),
            ),
        )

        tsr_node = Node(
            node_name=name,
            node_id=str(port),
            host="0.0.0.0",
            port=int(port),
            peers=peers,
            validator_data=my_data,
            is_builder=is_builder,
            is_validator=is_validator,
        )

        block = Block.from_random(0)
        block.header = Header.decode(Bytes.fromhex(dev_spec["genesis_header"]))
        block.save(db)

        block_producer = BlockProducer(tsr_node, db)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(tsr_node.initialize())
            if tsr_node.is_builder:
                tg.create_task(wp_producer(tsr_node, db))
            else:
                tg.create_task(block_producer.run())


    except KeyboardInterrupt:
        logger.info(f"👋 ({name}) Shutting down JAM node 🔐")
    except Exception as e:
        logger.exception(f"💥 ({name}) Fatal error", error=str(e)[:100])
        raise
