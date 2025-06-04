from dataclasses import dataclass
from typing import cast

from sphinx.ext.autodoc.typehints import augment_descriptions_with_types

from jam.config.logging import logger
from jam.network.quic import QuicServerProtocol
from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.types.base.null import Null
from jam.types.base.sequences.vector import Vector
from jam.types.extrinsics import assurances
from jam.types.extrinsics.assurances import Assurance, AvailAssurance, AssurancesExtrinsic

from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.utils.codec import Codable


@decodable_dataclass
@dataclass
class CE141Data(Codable, JsonSerde):
    assurance : Assurance


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

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE141

    async def transmit(self, node: Node, data: CE141Data):
        """ Transmit assurance, From Assurer (client) to Validator (server) """


        stream = self._prefix.encode() + data.encode()

        # logger.info(f"Transmitting assurance {data} to the {len(node.connections)} validators with prefix {self._prefix}")


        # TODO: send assurance to particular (that share the report) validator

        responses = Vector([])
        for peer in node.peer_conn:
            client = node.peer_conn[peer][1]
            data = await client.stream_and_close(message=stream)
            logger.info("sending assurance on ", data)
            responses.append(data)

        return responses


    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        data, offset = CE141Data.decode_from(buffer)
        data = cast(CE141Data, data)

        logger.info(f"Receive assurance {data} from the assurer")

        # TODO: Save the assure and signature in the database
        assurance : AvailAssurance = AvailAssurance(anchor=, bitfield=, validator_index=node.index, signature= )


    def client_intercept(self, node: Node, buffer: bytes, stream_id: int) -> Assurance:
        return Null