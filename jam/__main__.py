import asyncio
import uvloop
from jam.config.logging import setup_logging, get_logger
from jam.config.settings import settings

logger = get_logger(__name__)


async def main() -> None:
    # Setup logging
    setup_logging()

    logger.info(
        "Starting JAM node",
        node_name=settings.NODE_NAME,
        listen_address=settings.LISTEN_ADDRESS,
        listen_port=settings.LISTEN_PORT,
    )

    try:
        # Initialize components
        # TODO: Add initialization code

        # Start main loop
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down JAM node")
    except Exception as e:
        logger.exception("Fatal error", error=str(e))
        raise


if __name__ == "__main__":
    # Use uvloop for better performance
    uvloop.install()
    asyncio.run(main())
