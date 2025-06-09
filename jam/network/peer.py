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
    def get_validator_index(self):
        from jam.state.state import state

        for i,val in enumerate(state.kappa):
            if val.bandersnatch == self.data.bandersnatch:
                return i

        raise ValueError("No validator found with matching bandersnatch key.")

    def __init__(self, id: str, data: ValidatorData):
        self.id = id
        self.data = data

    def __repr__(self):
        return f"Peer(host={self.data.metadata.host}, port={self.data.metadata.port}, name={self.data.metadata.name})"