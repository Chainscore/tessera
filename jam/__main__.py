import asyncio
import json
import logging
import os
import time
from math import floor

from dotenv import load_dotenv
from tsrkit_types.bytes import Bytes

from jam.config.data_stores import data_stores
from jam.config.keys import setup_keys
from jam.config.logging import setup_logging, logger
from jam.config.chainspec import chain_config
from rockstore import RockStore

from jam.consensus.grandpa.finality import Finality
from jam.consensus.sync import sync
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
    load_dotenv(".env")
    load_dotenv(env)

    name = os.environ["NODE_NAME"]
    port = os.environ["PORT"]
    seed = os.environ["SEED"]

    if not name or not port:
        raise ValueError(f"Name or Port not found in {env}")

    # Setup logging with environment detection
    environment = os.environ.get("ENVIRONMENT", "development")
    log_level = os.environ.get("LOG_LEVEL", None)
    
    setup_logging(
        theme=theme, 
        node_name=name,
        environment=environment,
        min_level=getattr(logging, log_level.upper()) if log_level else None
    )

    logger.info(
        "Starting JAM node",
        node_name=name,
        port=port,
        spec=chain_config.name,
        environment=environment,
        is_builder=is_builder,
        is_validator=is_validator
    )
    try:
        if start_genesis:
            # Store current timestamp in ts.genesis
            genesis_ts = time.time()
            with open("genesis_ts", "w") as f:
                f.write(str(floor(genesis_ts)))
        else:
            # We'll be syncing later, here just ensure ts.genesis exists
            genesis_ts = int(open("genesis_ts", "r").read())
            if genesis_ts == 0:
                raise ValueError("Genesis timestamp not found. Exiting...")

        # Set genesis state
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        data_stores.configure_db_paths("db/" + str(int(port)))
        state = setup_state(data_stores.main_db, "dev-spec.json")
        keys = setup_keys(int(os.environ["SEED"]))

        # Genesis specs
        dev_spec = json.load(open(genesis_path))

        peers = [
            Peer(
                port=int(val.metadata.port),
                host=".".join([str(int(val)) for val in val.metadata.host]),
                san=val.metadata.name,
            )
            for val in state.kappa
        ]

        tsr_node = Node(
            node_name=name,
            node_id=str(port),
            host="0.0.0.0",
            port=int(port),
            peers=peers,
            validator_data=ValidatorData(
                keys.bandersnatch_public,
                keys.ed25519_public,
                BlsPublic(bytes(144)),
                ValidatorMetadata(
                    name=Bytes[10](bytes(10)),
                    protocol=Uint[16](2 ** 16 - 1),
                    host=IPAddress([U8(0), U8(0), U8(0), U8(0)]),
                    port=U16(port),
                ),
            ),
            is_builder=is_builder,
            is_validator=is_validator,
        )

        block = Block.from_random(0)
        block.header = Header.decode(Bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(data_stores.main_db)
        Finality.set_head(header_hash, data_stores.main_db)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(tsr_node.initialize())
            # tg.create_task(sync(state))
            if tsr_node.is_builder:
                tg.create_task(wp_producer(tsr_node, data_stores.main_db))
            else:
                tg.create_task(BlockProducer(tsr_node, data_stores.main_db).run())


    except KeyboardInterrupt:
        logger.info(
            "JAM node shutting down gracefully",
            node_name=name,
            port=port,
            reason="keyboard_interrupt"
        )
    except Exception as e:
        logger.critical(
            "JAM node fatal error",
            node_name=name,
            port=port,
            error=str(e)[:200],
            error_type=type(e).__name__
        )
        raise
