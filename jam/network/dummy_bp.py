
import asyncio
from .node import Node
from jam.config.logging import logger

async def produce_blocks(node: Node):
    """Continuously produces blocks and announces them."""
    block_number = 0
    while True:
        if not node.is_initialized:
            logger.info(f"🔄 ({node.name}) Node is not initialized, skipping block production")
            await asyncio.sleep(4)
            continue

        if (block_number + node.port) % len(node.peers) == 0:
            block_hash = f"Hash#{block_number}"
            logger.info(f"⛏️ ({node.name}) Producing Block {block_hash}")
            for client in node.connections:
                await client.send_message(f"Block from {node.name}: {block_number}")
        else:
            logger.info(f"🔄 ({node.name}) Skipping Block {block_number}")

        await asyncio.sleep(6)
        block_number += 1