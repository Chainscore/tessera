import asyncio
import json
from jam.config.logging import setup_logging, logger
from jam.chainspec import chain_config
from jam.consensus.safrole.safrole import Safrole
from jam.db.kv import KVStore
from jam.network.peer import Peer
from jam.network.node import Node
from jam.consensus.bp_engine import BlockProducer
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint
from jam.state.state import State
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

async def main(name: str, genesis_path: str, db_path: str, port: int, start_genesis: bool, theme: str) -> None:
    # Setup logging
    setup_logging(theme=theme)

    logger.info(
        f"Starting {name} node",
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
            node_name=name, 
            node_id=port, 
            host="0.0.0.0", 
            port=port, 
            peers=peers,
            validator_data=my_data
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

            block_producer = BlockProducer(tsr_node, db)

            async with asyncio.TaskGroup() as tg:
                tg.create_task(tsr_node.initialize())
                tg.create_task(block_producer.run())
        else:
            # TODO: Sync from peers
            raise NotImplementedError("Syncing from peers is not implemented yet")

    
    except KeyboardInterrupt:
        logger.info(f"👋 ({name}) Shutting down JAM node 🔐")
    except Exception as e:
        logger.exception(f"💥 ({name}) Fatal error", error=str(e)[:100])
        raise
