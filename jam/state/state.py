import hashlib
from typing import List
from jam.state.components.gamma import GammaK
from jam.state.components.sigma import Sigma
from jam.state.utils.key_constructor import construct_state_key
from jam.state.merkle import StateMerkle
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.block import Block
from jam.types.header import Header
from jam.types.protocol.crypto import Hash
from jam.utils.constants import EPOCH_LENGTH, TICKET_SUBMISSION_END

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
            construct_state_key(14): Bytes(self.theta.encode()),
            construct_state_key(15): Bytes(self.xi.encode()),
        }
    
    def generate_root(self) -> ByteArray32:
        """Generate the root hash of the state"""
        return self._merkle.merkelize(self.transform())
    
    def get_merkle_nodes(self) -> dict:
        """Get all nodes in the state Merkle trie"""
        return self._merkle.get_nodes()
    
    def verify_vrf(public_key: bytes, message: bytes, proof: bytes) -> bool:
        return True

    def compute_ring_root(keys: List[bytes]) -> bytes:
        sorted_keys = sorted(keys)
        return hashlib.sha256(b''.join(sorted_keys)).digest()

    def vrf_output(proof: bytes) -> bytes:
        return hashlib.sha256(proof).digest()


    def safrole_state_transition(
        self,
        block: Block,
    ) -> None:
        new_state = self.copy()
        
        # Timekeeping
        new_state.tau = block.header.tickets_mark
        # Update entropy
        new_state.eta[0] = hashlib.sha256(self.eta[0] + self.vrf_output(block.header.H_v)).digest()
        # Process them tickets
        if (block.header.slot % EPOCH_LENGTH) < TICKET_SUBMISSION_END:
            for validator_idx, ticket_proof in block.extrinsic.tickets:
                if validator_idx < len(self.kappa):
                    validator_key = self.kappa[validator_idx]
                    if self.verify_vrf(validator_key.bandersnatch_key, self.gamma_z, ticket_proof):
                        ticket = (self.vrf_output(ticket_proof), validator_idx)
                        new_state.gamma_a.append(ticket)
            
            new_state.gamma_a.sort(key=lambda x: x[0])
        # Epoch transition
        old_epoch = self.tau // EPOCH_LENGTH
        new_epoch = block.header.H_t // EPOCH_LENGTH
        if new_epoch > old_epoch:
            # Rotate validator sets and sort kappa
            new_state.lambada = self.kappa
            new_kappa = [
                k for k in new_state.gamma.k
                if not any(k.ed25519 == off for off in self.psi.o)
            ]
            new_kappa.sort(key=lambda k: k.bandersnatch_key)  # Sort validators
            new_state.kappa = new_kappa
            new_state.gamma_k = GammaK([])
            new_state.gamma_z = self.compute_ring_root([k.bandersnatch for k in new_state.kappa])
            # Update entropy
            new_state.eta = [new_state.eta[0], self.eta[0], self.eta[1], self.eta[2]]
        

        # Update seal keys using sorted kappa
        if len(new_state.gamma_a) >= EPOCH_LENGTH:
            new_state.gamma_s = [t[0] for t in new_state.gamma_a[:EPOCH_LENGTH]]
        else:
            sorted_keys = sorted([k.bandersnatch_key for k in new_state.kappa])
            new_state.gamma_s = [
                sorted_keys[i % len(sorted_keys)]
                for i in range(EPOCH_LENGTH)
            ]


        return new_state
