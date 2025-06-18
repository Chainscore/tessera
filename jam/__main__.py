import asyncio
import json
import logging
import os
import time
from math import floor

from dotenv import load_dotenv
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U16, U8, Uint

from jam.config.keys import setup_keys
from jam.config.logging import setup_logging, logger
from jam.config.chainspec import chain_config

from jam.consensus.grandpa.finality import Finality
from jam.config.settings import settings, setup_setting
from jam.execution.pvm.code import Code

from jam.network.peer import Peer
from jam.network.node import Node
from jam.network.utils.dummy_wpb import wp_producer

from jam.consensus.bp_engine import BlockProducer
from jam.state.state import setup_state
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Hash
from jam.types.protocol.core import Balance, Gas, BlobLength, ServiceId
from jam.types.state.delta import Ai, Ao, Timestamps, LookupTable
from jam.types.protocol.crypto import Ed25519Public, Hash
from jam.types.block import Block, Header
from jam.types.protocol.validators import (
    IPAddress,
    ValidatorData,
    ValidatorMetadata,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.types.state.delta import AccountMetadata


async def main(
    genesis_path: str,
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

    # Setup Settings
    setup_setting(name, int(port))

    # Get DB
    main_db = settings.db

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
        state = setup_state(main_db, "dev-spec.json")
        keys = setup_keys(int(seed))

        # Genesis specs
        dev_spec = json.load(open(genesis_path))

        # TODO: Fix peers
        peers = [
            Peer(
                id=bytes.decode(val.metadata.name, 'utf-8'),
                data=val
            )
            for val in state.kappa
            if val.metadata.port != port
        ]

        # TODO: Fix Node
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

        block = Block.from_random(0)
        block.header = Header.decode(Bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)

        pc = bytes(
            [0, 0, 22, 124, 121, 81, 25, 1, 7, 40, 2, 0, 149, 17, 255, 70, 1, 1, 100, 23, 51, 8, 1, 50, 0, 69, 147,
             18])

        c0_authorized_code = [0, 0, 21, 124, 121, 81, 9, 6, 40, 2, 0, 149, 17, 255, 70, 1, 1, 100, 23, 51, 8, 1, 50,
                              0,
                              165, 73, 9]

        code = Code(code=pc, read=b"", r_write=b"", z=0, s=100)
        bytecode = code.encode()
        service_code = Bytes(b"").encode() + bytecode
        code_hash = Hash.blake2b(service_code)

        state.delta[ServiceId(42)].service = AccountMetadata(code_hash=code_hash, balance=Balance(1_000_000),
                                                             gas_limit=Gas(1_000), min_gas=Gas(1_000), num_i=Ai(0),
                                                             num_o=Ao(0))
        state.delta[ServiceId(42)].service.code_hash = Bytes(service_code)
        state.delta[ServiceId(42)].lookup[
            LookupTable(hash=code_hash, length=BlobLength(len(service_code)))] = Timestamps([state.tau])

        wi_pc = bytes(
            [0, 0, 90, 51, 12, 149, 27, 0, 112, 254, 124, 117, 6, 40, 2, 200, 199, 3, 149, 51, 7, 200, 203, 4, 130,
             57, 123, 73, 149, 204, 8, 172, 92, 240, 100, 194, 40, 2, 200, 203, 7, 51, 8, 20, 9, 255, 255, 255, 255,
             255, 0, 0, 0, 51, 10, 5, 51, 11, 51, 12, 10, 18, 86, 23, 255, 9, 200, 114, 2, 40, 6, 51, 7, 40, 2, 149,
             23, 0, 112, 254, 100, 40, 10, 19, 149, 23, 0, 112, 254, 51, 8, 50, 0, 133, 148, 164, 146, 74, 1, 164,
             138, 84, 161, 66, 1]
        )

        wi_code = Code(code=wi_pc, read=b"", r_write=b"", z=0, s=(1024 * 100))
        wi_bytecode = wi_code.encode()
        wi_service_code = Bytes(b"").encode() + wi_bytecode
        wi_code_hash = Hash.blake2b(wi_service_code)
        wi_service = ServiceId(1)

        state.delta[wi_service].service = AccountMetadata(code_hash=wi_code_hash, balance=Balance(1_000_000),
                                                          gas_limit=Gas(1_000), min_gas=Gas(1_000), num_i=Ai(0),
                                                          num_o=Ao(0))
        state.delta[wi_service].service.code_hash = Bytes(wi_service_code)
        state.delta[wi_service].lookup[
            LookupTable(hash=wi_code_hash, length=BlobLength(len(wi_service_code)))] = Timestamps([state.tau])
        async with asyncio.TaskGroup() as tg:
            tg.create_task(tsr_node.initialize())
            # tg.create_task(sync(state))
            if tsr_node.is_builder:
                tg.create_task(wp_producer(tsr_node, main_db))
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
