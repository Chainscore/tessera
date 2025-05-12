from dataclasses import dataclass
from typing import cast
from jam.config.logging import logger
from jam.network.quic import QuicServerProtocol

from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.extrinsics.assurances import AvailAssurance
from tests.dummy.dummy_extrinsics import create_dummy_assurances


@decodable_dataclass
@dataclass
class Assurance(Codable, JsonSerde):
    header_hash : AvailAssurance.anchor
    bitfield : AvailAssurance.bitfield
    ed25519_signature : AvailAssurance.signature

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
        """share assurance for particular work report work-package's chunks"""
        message = self._prefix.encode() + data.assurance.encode()
        logger.info(f"Give assurance for work report by the validators")

    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """intercept Assurer signature for work-report from validators  """
        data, offset = CE141Data.decode_from(buffer)
        data = cast(CE141Data, data)

        logger.info(f"Receive assurance for work report from Assurer")

        assurance = create_dummy_assurances()

        ack = self._prefix.encode() + assurance.encode()
        server.stream_and_close(stream_id, ack)

    def client_intercept(self, buffer: bytes, stream_id: int):
        """ intercept assurance list"""
        logger.info(f"recived validator assurance")

        # TODO: Process & Save Work report