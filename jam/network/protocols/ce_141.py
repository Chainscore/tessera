from dataclasses import dataclass
from typing import cast
from jam.config.logging import logger
from jam.network.quic import QuicServerProtocol
from jam.types.base.sequences.vector import Vector
from jam.types.base.null import Null
from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.extrinsics.assurances import Assurance

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

    def transmit(self, node: Node, data: CE141Data):
        """ Transmit assurance, From Assurer (client) to Validator (server) """

        stream = self._prefix.encode() + data.encode()

        logger.info(f"Transmitting assurance {data} to the {len(node.connections)} validators with prefix {self._prefix}")


        # TODO: send assurance to particular (that share the report) validator

        responses = Vector([])
        for client in node.connections:
            data = client.stream_and_close(message=stream)
            responses.append(data)

        return responses


    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        data, offset = CE141Data.decode_from(buffer)
        data = cast(CE141Data, data)

        logger.info(f"Receive assurance {data} from the assurer")

        # TODO: Save the assure and signature in the database

    def client_intercept(self, node: Node, buffer: bytes, stream_id: int) -> Assurance:
        return Null