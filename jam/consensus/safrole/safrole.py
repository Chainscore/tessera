from typing import List, Union
from jam.consensus.safrole.errors import SafroleError
from jam.consensus.safrole.gamma import GammaK
from jam.state.state import State
from jam.types.block import Block
from jam.utils.constants import EPOCH_LENGTH, TICKET_SUBMISSION_END
from jam.types.protocol.crypto import BandersnatchPublic, BandersnatchRingRoot, Hash

class Safrole:
    @staticmethod
    def verify_vrf(public_key: bytes, message: bytes, proof: bytes) -> bool:
        # TODO: Implement VRF verification after VRF module is added
        return True

    @staticmethod
    def compute_ring_root(keys: List[BandersnatchPublic]) -> BandersnatchRingRoot:
        sorted_keys = sorted(keys)
        return Hash.sha256(b''.join(sorted_keys)).digest()

    @staticmethod
    def vrf_output(proof: bytes) -> bytes:
        return Hash.sha256(proof).digest()
    
    @staticmethod
    def transition(pre_state: State, block: Block) -> Union[State, SafroleError]:
        pass
        # new_state = pre_state.copy()
        
        # # Timekeeping
        # new_state.tau = block.header.tickets_mark
        # # Update entropy
        # new_state.eta[0] = Hash.sha256(new_state.eta[0] + Hash.sha256(block.header.H_v)).digest()
        # # Process them tickets
        # if (block.header.slot % EPOCH_LENGTH) < TICKET_SUBMISSION_END:
        #     for validator_idx, ticket_proof in block.extrinsic.tickets:
        #         if validator_idx < len(new_state.kappa):
        #             validator_key = new_state.kappa[validator_idx]
        #             if State.verify_vrf(validator_key.bandersnatch_key, new_state.gamma_z, ticket_proof):
        #                 ticket = (State.vrf_output(ticket_proof), validator_idx)
        #                 new_state.gamma_a.append(ticket)
        #     new_state.gamma_a.sort(key=lambda x: x[0])
        
        # # Epoch transition
        # old_epoch = new_state.tau // EPOCH_LENGTH
        # new_epoch = block.header.H_t // EPOCH_LENGTH
        # if new_epoch > old_epoch:
        #     # Rotate validator sets and sort kappa
        #     new_state.lambada = new_state.kappa
        #     new_kappa = [
        #         k for k in new_state.gamma.k
        #         if not any(k.ed25519 == off for off in new_state.psi.o)
        #     ]
        #     new_kappa.sort(key=lambda k: k.bandersnatch_key)  # Sort validators
        #     new_state.kappa = new_kappa
        #     new_state.gamma_k = GammaK([])
        #     new_state.gamma_z = State.compute_ring_root([k.bandersnatch for k in new_state.kappa])
        #     # Update entropy
        #     new_state.eta = [new_state.eta[0], new_state.eta[0], new_state.eta[1], new_state.eta[2]]

        # # Update seal keys using sorted kappa
        # if len(new_state.gamma_a) >= EPOCH_LENGTH:
        #     new_state.gamma_s = [t[0] for t in new_state.gamma_a[:EPOCH_LENGTH]]
        # else:
        #     sorted_keys = sorted([k.bandersnatch_key for k in new_state.kappa])
        #     new_state.gamma_s = [
        #         sorted_keys[i % len(sorted_keys)]
        #         for i in range(EPOCH_LENGTH)
        #     ]
        
        # return new_state

