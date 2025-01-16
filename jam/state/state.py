from jam.state.components.sigma import Sigma
from jam.state.utils.key_constructor import construct_state_key
from jam.state.merkle import StateMerkle
from jam.types.base.sequences.byte_array import ByteArray32
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
            construct_state_key(1): self.alpha.encode(),
            construct_state_key(2): self.beta.encode(),
            construct_state_key(3): self.gamma.encode(),
            construct_state_key(4): self.delta.encode(),
            construct_state_key(5): self.psi.encode(),
            construct_state_key(6): self.eta.encode(),
            construct_state_key(7): self.iota.encode(),
            construct_state_key(8): self.kappa.encode(),
            construct_state_key(9): self.lambada.encode(),
            construct_state_key(10): self.rho.encode(),
            construct_state_key(11): self.tau.encode(),
            construct_state_key(12): self.chi.encode(),
            construct_state_key(13): self.pi.encode(),
            construct_state_key(14): self.theta.encode(),
            construct_state_key(15): self.xi.encode(),
        }
    
    def generate_root(self) -> ByteArray32:
        """Generate the root hash of the state"""
        return self._merkle.merkelize(self.transform())
    
    def get_merkle_nodes(self) -> dict:
        """Get all nodes in the state Merkle trie"""
        return self._merkle.get_nodes()
