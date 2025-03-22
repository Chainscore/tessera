import asyncio
import json
from jam.config.logging import setup_logging, logger
from jam.chainspec import chain_config
from jam.consensus.safrole.safrole import Safrole
from jam.network.peer import Peer
from jam.network.node import Node
from jam.network.dummy_bp import produce_blocks
from jam.state.state import State
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata

async def main(genesis: str, port: int) -> None:
    # Setup logging
    setup_logging()

    logger.info(
        "Starting JAM node",
        spec=chain_config.name,
        listen_port=port,
    )
    try:
        # Initialize components
        peerlist = json.load(open(genesis))["peers"]
        peers = [Peer(port=pr["port"], host=pr["host"], san=pr["id"]) for pr in peerlist]

        tsr_node = Node(node_name=port, node_id=port, host="0.0.0.0", port=port, peers=peers)

        validators = [ValidatorData(
            bandersnatch=BandersnatchPublic(pr["bandersnatch_public"]),
            ed25519=Ed25519Public(pr["ed25519_public"]),
            bls=BlsPublic(pr["bls_public"]),
            metadata=ValidatorMetadata(bytes(128))
        ) for pr in peerlist]

        genesis_state = State.genesis(validators, Safrole.arrange_fallback(bytes(32), validators))

        async with asyncio.TaskGroup() as tg:
            tg.create_task(tsr_node.initialize())
            tg.create_task(produce_blocks(tsr_node))
    
    except KeyboardInterrupt:
        logger.info("Shutting down JAM node")
    except Exception as e:
        logger.exception("Fatal error", error=str(e))
        raise
