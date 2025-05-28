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

    def __init__(self, id: str, data: ValidatorData):
        self.id = id
        self.data = data

    def __repr__(self):
        return f"Peer(host={self.data.metadata.host}, port={self.data.metadata.port}, name={self.data.metadata.name})"