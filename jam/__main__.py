import asyncio
import json
import logging
import os
import time

from dotenv import load_dotenv
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U16, U8, Uint

from jam.config.keys import setup_keys
from jam.config.logging import setup_logging, logger
from jam.config.chainspec import chain_config,get_chain_config

from jam.consensus.bp_engine import BlockProducer
from jam.consensus.grandpa.finality import Finality
from jam.config.settings import setup_setting

from jam.network.peer import Peer
from jam.network.node import Node

from jam.operations import Builder
from jam.operations.utils.state_update import update_state

from jam.state.state import setup_state
from jam.types.protocol.crypto import BlsPublic
from jam.types.block import Block
from jam.types.protocol.validators import (
    IPAddress,
    ValidatorData,
    ValidatorMetadata,
)

from jam.types.state.delta import AccountMetadata
from jam.utils.constants import GENESIS_TS, SLOT_PERIOD, EPOCH_LENGTH


async def main(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
) -> None:
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS         # Actual Genesis time for JAM Common Era
    init_ts = int((time.time() - genesis_ts) // SLOT_PERIOD)
    init_ep = int(init_ts // EPOCH_LENGTH)

    if not is_builder and not is_validator:
        is_validator=True
    # ---------- LOAD ENVIRONMENT ----------
    # load_dotenv(".env")
    # load_dotenv(env,override=True)

    name = os.environ["NODE_NAME"]
    port = os.environ["PORT"]
    seed = os.environ["SEED"]

    if not name or not port:
        raise ValueError(f"Name or Port not found in {env}")

    # ---------- SETUP LOGGING ----------
    environment = os.environ.get("ENVIRONMENT", "development")
    log_level = os.environ.get("LOG_LEVEL", None)

    setup_logging(
        theme=theme,
        node_name=name,
        environment=environment,
        min_level=getattr(logging, log_level.upper()) if log_level else None
    )

    # ---------- SETUP SETTINGS ----------
    settings = setup_setting(name, int(port))

    main_db = settings.db

    logger.info(
        "Starting JAM node",
        name=name,
        port=port,
        ts=init_ts,
        epoch=init_ep,
        spec=chain_config.name,
        environment=environment,
        is_builder=is_builder,
        is_validator=is_validator
    )

    try:
        # Set genesis state
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync

        # logger.info(json.load(open(genesis_path))["genesis_state"])
        # Genesis specs
        state = setup_state(settings.state_db,genesis_path)
        state.store.disable_cache()
        update_state(state)

        keys = setup_keys(int(seed))


        # dev_spec = json.load(open(genesis_path))

        peers = [
            Peer(
                id=bytes.decode(val.metadata.name, 'utf-8'),
                data=val
            )
            for val in state.kappa
            if val.metadata.port != port
        ]

        tsr_node = Node(
            node_name=name,
            host="127.0.0.1",
            port=int(port),
            peers=peers,
            validator_data=ValidatorData(
                keys.bandersnatch_public,
                keys.ed25519_public,
                BlsPublic(bytes(144)),
                ValidatorMetadata(
                    name=Bytes[10](bytes(10)),
                    protocol=Uint[16](2 ** 16 - 1),
                    host=IPAddress([U8(127), U8(0), U8(0), U8(1)]),
                    port=U16(port),
                ),
            ),
            is_builder=is_builder,
            is_validator=is_validator,
        )

        block = Block.genesis()
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(tsr_node.initialize())
            # tg.create_task(sync(state))
            if tsr_node.is_builder:
                tg.create_task(Builder(tsr_node, settings).run())
            else:
                tg.create_task(BlockProducer(tsr_node, main_db).run())

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
        # Close db connections
        from jam.config.data_stores import data_stores
        data_stores.shutdown()

        raise
