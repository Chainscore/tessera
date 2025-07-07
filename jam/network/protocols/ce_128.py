from typing import List, cast, TYPE_CHECKING

from tsrkit_types import TypedVector, Enum, TypedArray

from jam.logging import get_logger
from jam.consensus.grandpa.finality import Finality
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.quic import QuicProtocol
from jam.types import HeaderHash, Block, TimeSlot

if TYPE_CHECKING:
    from jam.network.node import Node

from tsrkit_types.integers import U32
from tsrkit_types.struct import structure
from jam.network.base.protocol import NetworkProtocol, PrefixType

# Module-specific logger
logger = get_logger("network")

class Direction(Enum):
    AscExc = 0
    DesInc = 1

@structure
class Query:
    header: HeaderHash
    dir: Direction
    max_blocks: U32

@structure
class CE128Data:
    len: U32
    query: Query

    @property
    def is_valid(self):
        if len(self.query.encode()) == self.len:
            return True
        return False

Blocks = TypedVector[Block]

@structure
class CE128Response:
    len: U32
    blocks: Blocks

    @property
    def is_valid(self):
        print("VALIDITY", len(self.blocks.encode()), self.len)
        if len(self.blocks.encode()) == self.len:
            return True
        return False


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

    async def transmit(self, node: "Node", data: CE128Data, peer_conns: List | None = None):
        """Transmit Block Request"""

        query = data.query
        msg_a = query.encode()
        len_a = data.len.encode()

        logger.info(
            "Transmitting block request to node", num=len(peer_conns or node.peer_conn), header_hash=query.header, direction=query.dir, max_blocks=query.max_blocks,
        )

        transmitted_count = 0
        responses = []
        print("MAX BLOCKS", query.max_blocks)
        FixedBlocks = TypedArray[Block,10]

        if peer_conns is None:
            peer_conns = list(node.peer_conn.values())
        for peer in peer_conns:
            _, client = peer

            try:
                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                data = await client.close_and_wait(message=msg_a, stream_id=stream_id)

                transmitted_count += 1

                # print("HERE", data)
                # try:
                #     print("HERE 1")
                #     resp = FixedBlocks.decode(data)
                #     print("RESP", resp)
                # except Exception as e:
                #     print("PARSE ERR", e)
                responses.append(data)

                logger.debug(
                    "Block request transmitted to node",
                    stream_id=stream_id
                )
            except Exception as e:
                responses.append(None)
                logger.error(
                    "Failed to transmit state request",
                    node_name=node.name,
                    error=str(e),
                    error_type=type(e).__name__
                )

        logger.info(
            "Block request transmission completed",
            transmitted_to=transmitted_count,
        )

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Process Block Request"""
        node = server.node
        buffer = server.stream_buffer[stream_id][1:]

        try:
            from jam.settings import settings
            logger.debug(
                "Received block request",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )

            data, offset = CE128Data.decode_from(buffer)

            data = cast(CE128Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            data = data.query

            logger.info(
                "Processing block request", stream_id=stream_id,
                header_hash=data.header, direction=data.dir, max_blocks=data.max_blocks,
            )

            # TODO - Here we assume no gaps blocks, which is likely incorrect
            # To be thought upon

            # Get the start block
            start_block = Block.load(data.header, settings.main_db)
            start_timeslot = start_block.header.slot 
            latest = Finality.load_latest(settings.main_db)
            
            if data.dir == Direction.AscExc:
                _range = range(
                    start_timeslot+1,
                    min(int(latest.header.slot), int(start_timeslot) + int(data.max_blocks)) + 1 
                )
            else:
                _range = range(
                    start_timeslot,
                    max(0, int(start_timeslot) - int(data.max_blocks)),
                    -1
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
                    logger.error("Block not found against recorded header_hash", header_hash=hh, timeslot=data.header.slot)

            blocks_enc = all_blocks.encode()
            server.stream_and_close(stream_id=stream_id, message=self._prefix.encode() + blocks_enc)

            logger.info(
                "Blocks request completed successfully. Closed stream",
                stream_id=stream_id,
                len=len(blocks_enc)
            )

        except Exception as e:
            logger.error(
                "Error processing block request",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )

    def res_intercept(self, stream_id: int, client: QuicProtocol):
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]

        logger.info(
            "Block request ack received",
            stream_id=stream_id,
            buffer_size=len(buffer)
        )

        try:
            # print("buff",buffer.hex())
            data = CE128Response.decode(buffer[1:])
            length = U32.decode(buffer[1:5])
            block_buf = buffer[5:5+length]

            offset = 0
            buf_len = len((buffer[5:]))

            blocks = []
            while offset < buf_len:
                block, off = Block.decode_from(block_buf, offset)
                offset += off
                # print("bl ", off, block)
                blocks.append(block)

            # print("BLOCKS", blocks)
            print("len", length)
            # return Blocks.decode(buffer[5:5+length])

            # return buffer[5:5+length]
            data = cast(CE128Response, data)

            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            return bytes.fromhex(buffer.hex())
            # return data.blocks
        except Exception as e:
            print("ERROR", e)
            logger.error(Code.BAD_RESPONSE)
            return None
