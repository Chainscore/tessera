
from typing import cast, TYPE_CHECKING

from jam.types import WorkReport

if TYPE_CHECKING:
    from jam.network.node import Node

# from jam.config.logging import get_logger
from tsrkit_types import structure, Null
from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.protocols.ce_134 import OptCred
from jam.types.protocol.crypto import Ed25519Signature, HeaderHash
from tsrkit_types import TypedVector, U8, Uint, Option, Bool, U32
from jam.types.protocol.core import ValidatorIndex
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.utils.benchmark import benchmark, write_benchmarks_to_txt
from jam.types.block.extrinsics.assurances import AssurancesExtrinsic, AvailAssurance



# Module-specific logger
# logger = get_logger("network")

@structure
class Assurance:
    header_hash: HeaderHash
    bitfield : TypedVector[U8]
    validator_index : ValidatorIndex
    ed25519_signature: Ed25519Signature

@structure
class CE141Data:
    len : Uint[32]
    assurance : Assurance

    @property
    def is_valid(self):
        if len(self.assurance.encode()) == self.len:
            return True
        return False


OptBool = Option[Bool]

class AssuranceDistribution(NetworkProtocol):
    from jam.network.node import Node
    """
    CE-141 Assurance(Validators issue a signed statement, called an assurance) Distribution protocol enables each validator to broadcast an availability assurance for a work report.

    Protocol Flow:
        Assurer -> validator

        --> Assurance
        --> FIN
        <-- FIN
        
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-141-assurance-distribution

    """

    # TODO: Reimplement 141 properly
    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE141


    async def transmit(self, node: "Node", data: CE141Data):
        """ Transmit assurance, From Assurer (client) to Validator (server) """
        ...
        # try:
        #     print("inside transmit")
        #     msg = data.assurance.encode()
        #     print("message_length", len(msg))
        #     len_a = data.len.encode()
        #     print("check_length", data.len)
        # except Exception as e:
        #     print("error transmit", e)
        #     raise
        #
        #
        # transmitted_count = 0
        # responses = TypedVector[OptCred]([])
        # for peer in node.peer_conn:
        #     try:
        #         print("inside transmit port", peer.port)
        #         if int(peer.port) == 40004:
        #             print("inside 40002 transmit")
        #             logger.info("sending assurance to 40002")
        #             client = node.peer_conn[peer][1]

        #             # Send protocol prefix
        #             stream_id =  client.stream_and_keep_open(message=self._prefix.encode())
        #
        #             # Append prefix to stream buffer so that we know the stream for handling response
        #             client.stream_buffer[stream_id] = self._prefix.encode()
        #
        #             # Send Messages with their lengths
        #             client.stream_and_keep_open(message=len_a, stream_id=stream_id)
        #             res = await client.close_and_wait(message=msg, stream_id=stream_id)
        #
        #             transmitted_count += 1
        #
        #             logger.debud(
        #                 "Assurance transmitted to other validator",
        #                 node_name=node.name,
        #                 stream_id=stream_id,
        #                 header_hash=data.assurance.header_hash,
        #             )
        #
        #             responses.append(res)
        #
        #     except Exception as e:
        #         logger.error(
        #             "Failed to transmit work package bundle to other validator",
        #             node_name=node.name,
        #             error=str(e),
        #             error_type=type(e).__name__
        #         )
        #
        # logger.info(
        #     "Assurance transmit completed",
        #     node_name=node.name,
        #     transmitted_to=transmitted_count,
        #     total_assurance=len(node.peer_conn)
        # )
        #
        # return responses

    def req_intercept(self, stream_id: int, server: "QuicProtocol"):
        ...
    #     """ receive work report after transmit and process it and build assurances """
    # #     request for shard fot that particular work report
    # #     node =  server.node
    #     buffer = server.stream_buffer[stream_id]
    #
    #     assurance_extrinsic  = TypedVector([])
    #
    #     logger.debud(
    #         "Received assurance for each validator",
    #         stream_id=stream_id,
    #         buffer_size=len(buffer[1:])
    #     )
    #     data, offset = CE141Data.decode_from(buffer[1:])
    #     data = cast(CE141Data, data)
    #
    #     print("received assurance", data.encode(), buffer[1:])
    #     print("len assurance", data.assurance.encode(), U32(len(data.assurance.encode())))
    #
    #     if not data.is_valid:
    #         raise NetworkingError(Code.INVALID_DATA)
    #
    #     assurance_extrinsic.append(data.assurance)
    #
    #     # TODO: validator check for assurance which check all the property for assurances
    #     # logger.info("Validator Assurances if any condition for check assurances")
    #     # validator = validator()
    #     # validator.validate_assurance(assurance)




    def res_intercept(self, stream_id: int, client: QuicProtocol):
        # """ Intercept Acknowledgment for Assurance Extrinsic """
        # buffer = client.stream_buffer[stream_id]
        #
        # if buffer[1:] == b"":
        #     logger.info(f"assurance received on Node via stream_id:  {stream_id }")
        #     return OptBool(True)
        # return OptBool(False)
        ...

