from tsrkit_types import structure

from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType


@structure
class CE141Data:
    ...


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

    async def transmit(self, node: Node, data: CE141Data):
        """ Transmit assurance, From Assurer (client) to Validator (server) """
        ...


    def req_intercept(self, stream_id: int, server: QuicProtocol):
        ...

    def res_intercept(self, stream_id: int, client: QuicProtocol):
        ...
