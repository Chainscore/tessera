import asyncio
import json
from jam.config.logging import setup_logging, logger
from jam.chainspec import chain_config
from jam.consensus.safrole.safrole import Safrole
from jam.db.kv import KVStore
from jam.network.peer import Peer
from jam.network.node import Node
from jam.network.dummy_bp import block_producer
from jam.network.dummy_wpb import wp_producer

from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint
from jam.state.state import State
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

async def main(genesis_path: str, db_path: str, port: int, is_builder: bool, start_genesis: bool) -> None:
    # Setup logging
    setup_logging()

    logger.info(
        "Starting Tessera node",
        spec=chain_config.name,
        listen_port=port,
    )
    try:
        # Initialize components
        peerlist = json.load(open(genesis_path))["peers"]
        peers = [Peer(port=pr["port"], host=pr["host"], san=pr["id"]) for pr in peerlist]

        # Load validator data from seeds
        my_keys = json.load(open("seeds/keys.json"))[str(port)]
        ed25519_public = Ed25519PrivateKey.from_private_bytes(
                            bytes.fromhex(my_keys["ed25519_private"][2:])
                        ).public_key()

        bandersnatch_public = BandersnatchPublic((BandersnatchPoint.generator_point() * int.from_bytes(bytes.fromhex(my_keys["bandersnatch_private"][2:]), 'little')).point_to_string().hex())
        my_data = ValidatorData(bandersnatch_public, ed25519_public, BlsPublic(bytes(144)), ValidatorMetadata(bytes(128)))

        tsr_node = Node(
            node_name=str(port),
            node_id=str(port),
            host="0.0.0.0", 
            port=port, 
            peers=peers,
            validator_data=my_data,
            is_builder=is_builder
        )
        db = KVStore(db_path)

        if start_genesis:
            # Start from genesis
            genesis_vals = [ValidatorData(
                bandersnatch=BandersnatchPublic(pr["bandersnatch_public"]),
                ed25519=Ed25519Public(pr["ed25519_public"]),
                bls=BlsPublic(pr["bls_public"]),
                metadata=ValidatorMetadata(bytes(128))
            ) for pr in peerlist]

            state = State.genesis(genesis_vals, Safrole.arrange_fallback(ByteArray32(bytes(32)), genesis_vals))
            state.save(db)

            async with asyncio.TaskGroup() as tg:
                tg.create_task(tsr_node.initialize())
                if tsr_node.is_builder:
                    print("yay i am imposter")
                    tg.create_task(wp_producer(tsr_node, db))
                else:
                    tg.create_task(block_producer(tsr_node, db))

        else:
            # TODO: Sync from peers
            raise NotImplementedError("Syncing from peers is not implemented yet")


    except KeyboardInterrupt:
        logger.info("👋 Shutting down JAM node 🔐")
    except Exception as e:
        logger.exception("💥 Fatal error", error=str(e))
        raise
