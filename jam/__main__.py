import asyncio
import json
from typing import cast

from tsrkit_types.bytes import Bytes

from jam.config.logging import setup_logging, logger
from jam.config.chainspec import chain_config
from jam.config.settings import settings, setup_setting
from jam.execution.pvm.code import Code

from jam.network.peer import Peer
from jam.network.node import Node
from jam.network.utils.dummy_wpb import wp_producer

from jam.consensus.bp_engine import BlockProducer
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint
from jam.state.ghost import GhostState
from jam.state.state import setup_state
from jam.types.protocol.core import Balance, Gas, BlobLength, ServiceId
from jam.types.state.delta import Ai, Ao, Timestamps, LookupTable
from jam.types.protocol.crypto import Ed25519Public, Hash
from tsrkit_types.integers import U16, U8, Uint
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic
from jam.types.block import Block, Header
from jam.types.protocol.validators import (
    IPAddress,
    ValidatorData,
    ValidatorMetadata,
    ValidatorsData,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.types.state.delta import AccountMetadata


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

    # Setup Settings
    setup_setting(name, port)

    # Get DB
    main_db = settings.db

    logger.info(
        f"Starting {name} node",
        spec=chain_config.name,
        listen_port=port,
        main_db=main_db.path
    )

    try:
        # Initialize components
        genesis = json.load(open(genesis_path))
        peerlist = genesis["peers"]
        peers = []

        for pr in peerlist:
            raw = bytes.fromhex(pr["metadata"][2:])  # strip "0x" and decode
            metadata = ValidatorMetadata(
                name=Bytes[10](raw[0:10]),
                protocol=U16.from_bytes(raw[10:12]),
                host=IPAddress([U8(b) for b in raw[12:16]]),
                port=U16.from_bytes(raw[16:18]),
                buffer=Bytes[110](raw[18:128])
            )

            if metadata.port == port:
                continue

            peer = Peer(
                id=pr["id"],
                data=ValidatorData(
                    bandersnatch=BandersnatchPublic(bytes.fromhex(pr["bandersnatch"][2:])),
                    ed25519=Ed25519Public(bytes.fromhex(pr["ed25519"][2:])),
                    bls=BlsPublic(bytes.fromhex(pr["bls"][2:])),
                    metadata=metadata
                )
            )
            peers.append(peer)

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
            # .hex()
        )
        my_data = ValidatorData(
            bandersnatch_public,
            ed25519_public,
            BlsPublic(bytes(144)),
            ValidatorMetadata(
                name=Bytes[10](bytes(10)),
                protocol=Uint[16](2 ** 15),
                host=IPAddress([U8(127), U8(0), U8(0), U8(1)]),
                port=U16(port),
            ),
        )

        tsr_node = Node(
            node_name=name,
            host="127.0.0.1",
            port=port,
            peers=peers,
            validator_data=my_data,
            is_builder=is_builder,
            is_validator=is_validator,
        )


        if start_genesis:
            # Start from genesis
            genesis_vals = ValidatorsData.from_json(peerlist)

            block = Block.from_random(0)
            block.header = Header.from_json(genesis["header"])
            block.save(main_db)

            # Set genesis state
            state = setup_state(GhostState.genesis(), main_db)

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
            state.delta[ServiceId(42)].lookup[LookupTable(hash=code_hash, length=BlobLength(len(service_code)))] = Timestamps([state.tau])

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

            block_producer = BlockProducer(tsr_node, main_db)

            async with asyncio.TaskGroup() as tg:
                tg.create_task(tsr_node.initialize())
                if tsr_node.is_builder:
                    tg.create_task(wp_producer(tsr_node))
                else:
                    tg.create_task(block_producer.run())

        else:
            # TODO: Sync from peers
            raise NotImplementedError("Syncing from peers is not implemented yet")

    except KeyboardInterrupt:
        logger.info(f"👋 ({name}) Shutting down JAM node 🔐")
    except Exception as e:
        # Close db connections
        from jam.config.data_stores import data_stores
        data_stores.shutdown()

        logger.exception(f"💥 ({name}) Fatal error", error=str(e)[:100])
        raise
