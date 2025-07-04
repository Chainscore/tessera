import asyncio
import json
import logging
import os
import time

from dotenv import load_dotenv
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U16, U8, Uint

from jam.logging import setup_logging, logger
from jam.network.base.certificate import generate_san
from jam.utils.chainspec import chain_config
from jam.settings import setup_setting

from jam.consensus.bp_engine import BlockProducer
from jam.consensus.grandpa.finality import Finality

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


    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env,override=True)

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
        min_level=getattr(logging, log_level.upper()) if log_level else None
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
        is_validator=is_validator
    )

    try:
        # Set genesis state
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, "dev-spec.json")
        state.store.disable_cache()
        update_state(state)

        # Genesis specs
        dev_spec = json.load(open(genesis_path))

        peers = [
            Peer(
                id=generate_san(val.ed25519),
                data=val
            )
            for val in state.kappa
            if val.metadata.port != port
        ]

        ip = IPAddress.from_str(host)
        tsr_node = Node(
            node_name=name,
            host=str(host),
            port=int(port),
            peers=peers,
            validator_data=ValidatorData(
                settings.bandersnatch_public,
                settings.ed25519_public,
                BlsPublic(bytes(144)),
                ValidatorMetadata(
                    name=Bytes[10](bytes(10)),
                    protocol=Uint[16](2 ** 16 - 1),
                    host=ip,
                    port=U16(port),
                ),
            ),
            is_builder=is_builder,
            is_validator=is_validator,
        )

        block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db)

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
        settings.clear()

        raise
