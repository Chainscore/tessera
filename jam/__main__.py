import asyncio
from datetime import datetime
from jam.config.logging import get_logger, setup_logging
from jam.config.settings import settings
from jam.chainspec import chain_config
from jam.types.protocol.crypto import Hash
from jam.utils.constants import EPOCH_LENGTH

logger = get_logger(__name__)


async def main() -> None:
    # Setup logging
    setup_logging()

    logger.info(
        "Starting JAM node",
        spec=chain_config.name,
        node_name=settings.NODE_NAME,
        listen_address=settings.LISTEN_ADDRESS,
        listen_port=settings.LISTEN_PORT,
    )
    try:
        # Initialize components
        # TODO: Add initialization code
        

        # Start main loop
        block_number = 0
        while True:
            logger.info(
                f"Processing block #{block_number}",
                block_hash=bytes(Hash.blake2b(f"{block_number:064x}".encode())).hex(),
                block_timestamp=datetime.now().isoformat(),
                epoch_number=block_number // EPOCH_LENGTH,
            )
            block_number += 1
            await asyncio.sleep(6)

    except KeyboardInterrupt:
        logger.info("Shutting down JAM node")
    except Exception as e:
        logger.exception("Fatal error", error=str(e))
        raise
