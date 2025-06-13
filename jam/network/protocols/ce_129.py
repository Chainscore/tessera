from typing import cast, TYPE_CHECKING

from tsrkit_types import Bytes, TypedVector, ByteArray, Dictionary

from jam.config.data_stores import data_stores
from jam.config.logging import get_logger
from jam.state.state import state
from jam.types import HeaderHash

if TYPE_CHECKING:
	from jam.network.quic.server import QuicServerProtocol
	from jam.network.node import Node

from tsrkit_types.integers import U32
from tsrkit_types.struct import structure
from jam.network.protocols.base import NetworkProtocol, PrefixType

# Module-specific logger
logger = get_logger("network")


@structure
class CE129Data:
	header: HeaderHash
	start: Bytes[31]
	end: Bytes[31]
	max_size: U32


class StateRequest(NetworkProtocol):
	"""
	CE 129 Protocol for handling State requests

	Protocol Flow:
		Node -> Node

		--> Header Hash ++ Key (Start) ++ Key (End) ++ Maximum Size
		--> FIN
		<-- [Boundary Node]
		<-- [Key ++ Value]
		<-- FIN
	Source:
		https://github.com/zdave-parity/jam-np/blob/main/simple.md#ce-129-state-request
	"""

	def __init__(self):
		super().__init__()
		self._prefix = PrefixType.CE129

	def transmit(self, node: "Node", data: CE129Data):
		"""Transmit State Request"""

		stream_data = self._prefix.encode() + data.encode()

		logger.info(
			"Transmitting state request to node", node_name=node.name,
			header_hash=data.header, start=data.start, end=data.end, max_len=data.max_size,
		)

		transmitted_count = 0
		for client in node.connections:
			try:
				stream_id = client.stream_and_close(message=stream_data)
				transmitted_count += 1

				logger.debug(
					"State request transmitted to node",
					node_name=node.name,
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
			"State request transmission completed",
			node_name=node.name,
			transmitted_to=transmitted_count,
		)

	def server_intercept(self, buffer: bytes, server: "QuicServerProtocol", stream_id: int):
		"""Intercept & Process Work Package on Guarantor (server)"""

		try:
			logger.debug(
				"Received state request",
				stream_id=stream_id,
				buffer_size=len(buffer)
			)

			data, offset = CE129Data.decode_from(buffer)
			data = cast(CE129Data, data)

			logger.info(
				"Processing state request", stream_id=stream_id,
				header_hash=data.header, start=data.start, end=data.end, max_len=data.max_size,
			)

			# TODO: we are ignoring the header hash, to be updated upon #194 [state variants]

			# Boundaries
			boundaries = set(state.TRIE.get_boundaries(data.start[0:31]))
			end_boundaries = state.TRIE.get_boundaries(data.end[0:31])
			# Join them, remove duplicates
			boundaries.update(end_boundaries)

			boundaries_data = TypedVector[Bytes[64]](list(boundaries)).encode()
			server.stream_and_keep_open(stream_id, boundaries_data)

			logger.debug(
				"Start and End boundaries shared successfully",
				stream_id=stream_id,
				len=len(boundaries_data)
			)

			# Key Vals
			_state_data_raw: dict = data_stores.state_db.get_range(data.start, data.end)
			state_data = Dictionary[Bytes[32], Bytes]({})
			for k, v in _state_data_raw:
				state_data[Bytes[32](k)] = Bytes(v)


			# Return all key val pairs
			key_val_data = state_data.encode()
			server.stream_and_close(stream_id, key_val_data)

			logger.info(
				"State response complete. Closed stream",
				stream_id=stream_id,
				size=len(key_val_data)
			)

		except Exception as e:
			logger.error(
				"Error processing state request",
				stream_id=stream_id,
				buffer_size=len(buffer),
				error=str(e),
				error_type=type(e).__name__
			)

	def client_intercept(self, buffer: bytes, stream_id: int):
		"""Intercept Acknowledgement"""

		logger.info(
			"State request ack received",
			stream_id=stream_id,
			buffer_size=len(buffer)
		)


