import asyncio

import aiohttp
import uvloop

from jam.config.logging import get_logger, setup_logging
from jam.config.settings import settings
from jam.state.state import State
from jam.state.utils.master_state import master_transition_state
from jam.types.block import Block
from tests.fixtures.dummy_state import create_dummy_state

logger = get_logger(__name__)


async def main(
    custom_arg=None, genesis: State = create_dummy_state(), start_slot=0, rpc_url=None
) -> None:
    # Setup logging
    setup_logging()

    logger.info(
        "Starting JAM node",
        msg=custom_arg,
        rpc_url=rpc_url,
        node_name=settings.NODE_NAME,
        listen_address=settings.LISTEN_ADDRESS,
        listen_port=settings.LISTEN_PORT,
    )
    try:
        # Initialize HTTP client session
        async with aiohttp.ClientSession() as session:
            # Initialize components
            # TODO: Add initialization code
            current_state = genesis
            current_slot = start_slot

            # Start main loop
            while True:
                await asyncio.sleep(1)
                logger.info("LOOP running")

                # Make request to the blocks endpoint if rpc_url is provided
                if rpc_url:
                    try:
                        blocks_url = f"{rpc_url}?slot={current_slot}"
                        logger.info("BLOCK", url=blocks_url)
                        async with session.get(blocks_url) as response:
                            if response.status == 200:
                                data = await response.json()
                                block = Block.from_json(data)
                                logger.info("Received blocks data", data=data)
                                current_state = master_transition_state(
                                    current_state, block
                                )
                                current_slot += 1

                            else:
                                logger.warning(
                                    "Failed to get blocks data",
                                    status_code=response.status,
                                    reason=response.reason,
                                )
                                break
                    except aiohttp.ClientError as e:
                        logger.error("HTTP request failed", error=str(e))
                        break

    except KeyboardInterrupt:
        logger.info("Shutting down JAM node")
    except Exception as e:
        logger.exception("Fatal error", error=str(e))
        raise


def run_main():
    uvloop.install()
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
