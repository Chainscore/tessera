from jam.network.node import Node
from jam.types import Block
from jam.config.logging import logger


class BlockAnnouncement:
    time_slot: int
    block_hash: str

async def announce_block(node: Node, block: Block):
    """
    UP 0 Protocol for announcing new blocks to peers.
    Args:
        node (Node): Node which needs to announce the block
        block (Block): Block to be announced
    """
    logger.info(f"Announcing blocks to {len(node.connections)} peers.")

    for client in node.connections:
        await client.send_message(block.encode())