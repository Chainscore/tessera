from typing import cast, TYPE_CHECKING

from tsrkit_types import Bytes, TypedVector, ByteArray, Dictionary, Enum

from jam.config.data_stores import data_stores
from jam.config.logging import get_logger
from jam.consensus.grandpa.finality import Finality
from jam.state.state import state
from jam.types import HeaderHash, Block, TimeSlot

if TYPE_CHECKING:
	from jam.network.quic.server import QuicServerProtocol
	from jam.network.node import Node

from tsrkit_types.integers import U32
from tsrkit_types.struct import structure
from jam.network.protocols.base import NetworkProtocol, PrefixType

# Module-specific logger
logger = get_logger("network")

class Direction(Enum):
	AscExc = 0
	DesInc = 1

@structure
class CE128Data:
	def __init__(self):
		self.start = None

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

	def transmit(self, node: "Node", data: CE128Data):
		"""Transmit State Request"""

		stream_data = self._prefix.encode() + data.encode()

		logger.info(
			"Transmitting block request to node", header_hash=data.header, direction=data.dir, max_blocks=data.max_blocks,
		)

		transmitted_count = 0
		for client in node.connections:
			try:
				stream_id = client.stream_and_close(message=stream_data)
				transmitted_count += 1

				logger.debug(
					"Block request transmitted to node",
					stream_id=stream_id
				)
			except Exception as e:
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

	def server_intercept(self, buffer: bytes, server: "QuicServerProtocol", stream_id: int):
		"""Intercept & Process Work Package on Guarantor (server)"""

		try:
			logger.debug(
				"Received block request",
				stream_id=stream_id,
				buffer_size=len(buffer)
			)

			data, offset = CE128Data.decode_from(buffer)
			data = cast(CE128Data, data)

			logger.info(
				"Processing block request", stream_id=stream_id,
				header_hash=data.header, direction=data.dir, max_blocks=data.max_blocks,
			)

			# TODO - Here we assume no gaps blocks, which is likely incorrect
			# To be thought upon

			# Get the start block
			start_block = Block.load(data.header, data_stores.main_db)
			start_timeslot = start_block.header.slot

			latest = Finality.load_latest(data_stores.main_db)

			end_timeslot = max(0, start_timeslot - data.max_blocks) if data.dir == Direction.DesInc else min(latest.header.slot, start_timeslot + data.max_blocks)
			# Get all header hashes in between
			all_blocks = TypedVector[Block]([])
			for ts in range(start_timeslot, end_timeslot):
				_header_hash = data_stores.main_db.get(TimeSlot(ts).encode())
				if _header_hash:
					_block = data_stores.main_db.get(_header_hash)
					if _block:
						all_blocks.append(_block)
					else:
						logger.error("Block not found against recorded header_hash", header_hash=_header_hash, timeslot=ts)
				else:
					logger.warning("Block missing", timeslot=ts)

			blocks_enc = all_blocks.encode()
			server.stream_and_close(stream_id, blocks_enc)

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

	def client_intercept(self, buffer: bytes, stream_id: int):
		"""Intercept Acknowledgement"""

		logger.info(
			"Block request ack received",
			stream_id=stream_id,
			buffer_size=len(buffer)
		)


