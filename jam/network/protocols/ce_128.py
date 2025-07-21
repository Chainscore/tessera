from typing import List, cast, TYPE_CHECKING

from tsrkit_types import TypedVector, Enum

from jam.logging import get_logger
from jam.finality.finality import Finality
from jam.network.base.error import NetworkingErrorCode
from jam.network.connection import NodeConnection
from jam.types import HeaderHash 


from tsrkit_types.integers import U32
from tsrkit_types.struct import structure
from jam.network.base.protocol import NetworkProtocol, PrefixType

# Module-specific logger
logger = get_logger("network")


class Direction(Enum):
    AscExc = 0
    DesInc = 1


@structure
class CE128Data:
    header: HeaderHash
    dir: Direction
    max_blocks: U32


class BlockRequest(NetworkProtocol):
    """
    CE 128 Protocol for handling Block requests

    Protocol Flow:
        Node -> Node

        --> Header Hash ++ Direction ++ Maximum Blocks
        --> FIN
        <-- [Block]
        <-- FIN
    Source:
        https://github.com/zdave-parity/jam-np/blob/main/simple.md#ce-128-block-request
    """

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE128

    async def transmit(self, data: CE128Data):
        """Transmit Block Request"""
        from jam.network.start import node 
        if not node: return

        stream_data = data.encode()
        logger.info("Transmitting block request to node", num=len(node.connection_ids), max_blocks=data.max_blocks)

        transmitted_count = 0
        responses = []

        for client in node.all_connected:
            try:
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                print("using stream", stream_id)
                data = await client.close_and_wait(message=stream_data, stream_id=stream_id)

                transmitted_count += 1
                responses.append(data)

                logger.debug("Block request transmitted to node", stream_id=stream_id)
            except Exception as e:
                responses.append(None)
                logger.error("Failed to transmit state request", error=e)

        logger.info(
            "Block request transmission completed",
            transmitted_to=transmitted_count,
        )

        return responses

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Process Block Request"""
        buffer = server.stream_buffer[stream_id][1:]

        try:
            from jam.settings import settings
            from jam.block.block import Block

            logger.debug("Received block request", stream_id=stream_id, buffer_size=len(buffer))

            data = CE128Data.decode(buffer)

            logger.info(
                "Processing block request",
                stream_id=stream_id,
                header_hash=data.header,
                direction=data.dir,
                max_blocks=data.max_blocks,
            )

            # TODO - Here we assume no gaps blocks, which is likely incorrect
            # To be thought upon

            # Get the start block
            start_block = Block.load(data.header, settings.main_db)
            start_timeslot = start_block.header.slot
            latest = Finality.load_latest(settings.main_db)

            if data.dir == Direction.AscExc:
                _range = range(
                    start_timeslot + 1,
                    min(
                        int(latest.header.slot),
                        int(start_timeslot) + int(data.max_blocks),
                    )
                    + 1,
                )
            else:
                _range = range(
                    start_timeslot,
                    max(0, int(start_timeslot) - int(data.max_blocks)),
                    -1,
                )

            # Get all header hashes in between
            all_blocks = TypedVector[Block]([])
            hh = data.header
            while hh != HeaderHash(32) and len(all_blocks) != int(data.max_blocks):
                _block = Block.decode(settings.main_db.get(Block.get_storage_key_block(hh)))
                if _block:
                    all_blocks.append(_block)
                    hh = _block.header.parent
                else:
                    logger.error(
                        "Block not found against recorded header_hash",
                        header_hash=_header_hash,
                        timeslot=ts,
                    )

            blocks_enc = all_blocks.encode()
            server.stream_and_close(stream_id=stream_id, message=self._prefix.encode() + blocks_enc)

            logger.info(
                "Blocks request completed successfully. Closed stream",
                stream_id=stream_id,
                len=len(blocks_enc),
            )

        except Exception as e:
            logger.error(
                "Error processing block request",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: NodeConnection):
        """Intercept Acknowledgement"""
        from jam.block.block import Block

        buffer = client.stream_buffer[stream_id]

        logger.info("Block request ack received", stream_id=stream_id, buffer_size=len(buffer))

        try:
            data = TypedVector[Block].decode(buffer[1:])
            return data
        except Exception as e:
            logger.error(NetworkingErrorCode.BAD_RESPONSE)
            return None
