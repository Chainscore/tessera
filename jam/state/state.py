from jam.state.components.sigma import Sigma
from jam.state.utils.key_constructor import construct_state_key
from jam.state.merkle import StateMerkle
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.protocol.crypto import Hash


class State(Sigma):
    """State implementation that adds Merklization to Sigma"""

    def __init__(self, **kwargs):
        """Initialize state with component kwargs"""
        super().__init__(**kwargs)
        self._merkle = StateMerkle(Hash.blake2b)

    def transform(self) -> dict:
        """Transform the state into a dictionary as defined in D.2"""
        # TODO - To add service-related state components when they Section 9 is implemented
        return {
            construct_state_key(1): Bytes(self.alpha.encode()),
            construct_state_key(2): Bytes(self.beta.encode()),
            construct_state_key(3): Bytes(self.gamma.encode()),
            construct_state_key(4): Bytes(self.delta.encode()),
            construct_state_key(5): Bytes(self.psi.encode()),
            construct_state_key(6): Bytes(self.eta.encode()),
            construct_state_key(7): Bytes(self.iota.encode()),
            construct_state_key(8): Bytes(self.kappa.encode()),
            construct_state_key(9): Bytes(self.lambada.encode()),
            construct_state_key(10): Bytes(self.rho.encode()),
            construct_state_key(11): Bytes(self.tau.encode()),
            construct_state_key(12): Bytes(self.chi.encode()),
            construct_state_key(13): Bytes(self.pi.encode()),
            construct_state_key(14): Bytes(self.nu.encode()),
            construct_state_key(15): Bytes(self.xi.encode()),
        }

    def generate_root(self) -> ByteArray32:
        """Generate the root hash of the state"""
        return self._merkle.merkelize(self.transform())

    def get_merkle_nodes(self) -> dict:
        """Get all nodes in the state Merkle trie"""
        return self._merkle.get_nodes()
