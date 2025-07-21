from tsrkit_types import TypedVector

from jam.network.base.certificate import generate_san
from jam.types import ValidatorIndex
from jam.types.protocol.validators import ValidatorData


class Peer:
    """
    Represents a peer in the network
    Args:
        id (str): Subject Alternative Name of the peer
        data (ValidatorData): Validator Data
    """

    id: str
    data: ValidatorData

    @property
    def peer_index(self):
        from jam.state.state import state

        for i, val in enumerate(state.kappa):
            if val.bandersnatch == self.data.bandersnatch:
                return ValidatorIndex(i)

        raise ValueError("No peer found with matching bandersnatch key.")

    @property
    def host(self):
        return str(self.data.metadata.host)

    @property
    def port(self):
        return int(self.data.metadata.port)

    @property
    def ed_key(self):
        return self.data.ed25519

    @property
    def name(self):
        return self.data.metadata.name

    def __init__(self, data: ValidatorData):
        self.id = generate_san(data.ed25519)
        self.data = data

    def __repr__(self):
        return f"Peer(host={self.host}, port={int(self.port)}, id=...{self.id[:4]})"

    def __str__(self):
        return f"Peer({self.host}:{int(self.port)})"

    def __int__(self):
        return f"Peer({int(self.port)})"
