from typing import List

from tsrkit_types import Option

from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.types import TicketsMark, TicketBody
from jam.types.block import TicketEnvelope, TicketsExtrinsic
from jam.types.state.eta import Eta
from jam.types.state.kappa import Kappa
from jam.types.state.lambda_ import Lambda_
from jam.types.state.sigma import Sigma
from tsrkit_types.integers import U64, U32
from tsrkit_types.null import Null
from jam.types.state.gamma import GammaS, GammaSTickets
from tsrkit_types.bytes import Bytes
from jam.types.block import Block
from jam.utils.constants import (
    EPOCH_LENGTH,
    TICKET_SUBMISSION_END,
    TICKET_ENTRIES_PER_VALIDATOR,
    MAX_TICKETS_PER_EXTRINSIC
)
from jam.types.protocol.crypto import BandersnatchPublic, BandersnatchRingVrfSignature, BandersnatchVrfSignature, Hash, Entropy
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from jam.types.state.gamma import GammaK, GammaSFallback, GammaA, GammaZ
from jam.types.protocol.validators import ValidatorData
from jam.types.protocol.epoch import MinValidatorData, ValidatorArray, EpochMark

# for ring root
from jam.ring_vrf.ring_proof.columns.columns import PublicColumnBuilder as PC
from jam.ring_vrf.ring_proof.helpers import Helpers as H


# for sign verification

class Safrole:
    @staticmethod
    def generate_ticket() -> TicketEnvelope:
        return TicketEnvelope(
            attempt=U32(0),
            signature=BandersnatchRingVrfSignature(bytes(784)),
        )

    @staticmethod
    def verify_vrf(message, proof) -> bool:
        # TODO: Implement VRF verification after VRF module is added
        # proof_ptr = [H.bls_g1_decompress(proof[:48]), H.bls_g1_decompress(proof[48 * 1: 48 * 2]),H.bls_g1_decompress(proof[48 * 2: 48 * 3]), H.bls_g1_decompress(proof[48 * 3:48 * 4]),H.to_scalar_int(proof[48 * 4 + (0 * 32): 48 * 4 + (1 * 32)]),H.to_scalar_int(proof[48 * 4 + (1 * 32): 48 * 4 + (2 * 32)]),H.to_scalar_int(proof[48 * 4 + (2 * 32): 48 * 4 + (3 * 32)]),H.to_scalar_int(proof[48 * 4 + (3 * 32): 48 * 4 + (4 * 32)]),H.to_scalar_int(proof[48 * 4 + (4 * 32): 48 * 4 + (5 * 32)]),H.to_scalar_int(proof[48 * 4 + (5 * 32): 48 * 4 + (6 * 32)]),H.to_scalar_int(proof[48 * 4 + (6 * 32): 48 * 4 + (7 * 32)]),H.bls_g1_decompress(proof[48 * 4 + (7 * 32):48 * 4 + (7 * 32) + 48]),H.to_scalar_int(proof[48 * 4 + (7 * 32) + 48:48 * 4 + (7 * 32) + 48 + 32]),H.bls_g1_decompress(proof[48 * 4 + (7 * 32) + 48 + 32:-98]), H.bls_g1_decompress(proof[-98:])]
        # rltn_to_proove=sw.decompress(message) #relation to proove
        # res_plus_seeed= sw.add(sw.from_twisted_edwards(SeedPoint), rltn_to_proove)
        #
        # ring_root = "0x85f9095f4abd040839d793d89ab5ff25c61e50c844ab6765e2c0b22373b5a8f6fbe5fc0cd61fdde580b3d44fe1be127197e33b91960b10d2c6fc75aec03f36e16c2a8204961097dbc2c5ba7655543385399cc9ef08bf2e520ccf3b0a7569d88492e630ae2b14e758ab0960e372172203f4c9a41777dadd529971d7ab9d23ab29fe0e9c85ec450505dde7f5ac038274cf" #example
        # C_px, C_py, C_s= H.bls_g1_decompress(ring_root[:98]) , H. bls_g1_decompress(ring_root[98:-98]) , H.bls_g1_decompress(ring_root[-98:])
        # fixed_cols_cmts=[C_px, C_py, C_s]
        #
        # verifier_key= {
        # 'g1':g1_points[0],
        # 'g2':H.altered_points(g2_points),
        #     'commitments':fixed_cols_cmts
        # }
        #
        # valid = Verify(proof_ptr, verifier_key, fixed_cols_cmts,rltn_to_proove, res_plus_seeed,SeedPoint,D)
        # # print("is any one:",valid.is_signtaure_valid())
        # print('am i called')
        # # return valid.is_signtaure_valid()

        return True

    @staticmethod
    def compute_ring_root(keys: List[BandersnatchPublic]) -> bytes:
        keys_as_bs_points = []
        for key in keys:
            point = BandersnatchPoint.string_to_point(bytes(key))  # or take key[2:] by skipping '0x'
            keys_as_bs_points.append((point.x, point.y))

        ring_root = PC()  # ring_root builder
        fxd_cols = ring_root.build(keys_as_bs_points)
        fxd_col_cs = bytearray.fromhex(H.bls_g1_compress(fxd_cols[0].commitment)) + bytearray.fromhex(
            H.bls_g1_compress(fxd_cols[1].commitment)) + bytearray.fromhex(H.bls_g1_compress(fxd_cols[2].commitment))

        return fxd_col_cs

    @staticmethod
    def vrf_output(signature: BandersnatchVrfSignature) -> Bytes[32]:
        if int.from_bytes(signature) == 0:
            return Bytes[32](signature[:32])
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
        return Bytes[32](vrf.ecvrf_proof_to_hash(bytes(signature))[:32])

    @staticmethod
    def transition(state: Sigma, block: Block, entropy: Bytes[32]) -> Sigma:
        pre_tau = state.tau
        # 1. Timekeeping
        if block.header.slot > state.tau:
            state.tau = block.header.slot
        elif state.tau > 0:
            raise SafroleError(
                SafroleErrorCode.BAD_SLOT,
                f"Slot {block.header.slot} is less than current tau {state.tau}",
            )

        old_epoch = int(pre_tau) // EPOCH_LENGTH
        new_epoch = int(block.header.slot) // EPOCH_LENGTH
        epoch_jump = new_epoch - old_epoch

        gamma = state.gamma

        # 3. Ticket Accumulation
        ticket_submission_active = (block.header.slot % EPOCH_LENGTH) < TICKET_SUBMISSION_END
        # Process the ticket.py before TICKET_SUBMISSION_END of the epoch, if the epoch is not jumped
        if ticket_submission_active and epoch_jump == 0:
            # Validate extrinsics
            Safrole.ensure_valid_ticket_extrinsics(block)
            # Accumulate them in gamma.a
            gamma.a += [
                TicketBody(
                    attempt=ticket.attempt, id=Safrole.vrf_output(ticket.signature)
                )
                for ticket in block.extrinsic.tickets
            ]
            gamma.a.sort(key=lambda x: x.id)
            gamma.a = GammaA(gamma.a[:EPOCH_LENGTH])
            # Check for duplicates
            if len(gamma.a) != len(list(set(gamma.a))):
                raise SafroleError(SafroleErrorCode.DUPLICATE_TICKET, "Duplicate ticket.py are not allowed")
        # We never expect ticket.py after TICKET_SUBMISSION_END
        if not ticket_submission_active:
            if len(block.extrinsic.tickets) > 0:
                raise SafroleError(SafroleErrorCode.UNEXPECTED_TICKET, "Tickets are not allowed after TICKET_SUBMISSION_END")

        # 4. Epoch transition
        if new_epoch > old_epoch:
            # 4.1. Rotate validators
            state.lambda_ = Lambda_(state.kappa)
            state.kappa = Kappa(gamma.k)
            filtered_validators=[]
            for k in state.iota:
                if k.ed25519 in state.psi.offenders:
                    # Offender found, replace with default ValidatorData
                    filtered_validators.append(ValidatorData(bandersnatch=Bytes[32](bytes(32)), ed25519=Bytes[32](bytes(32)), bls=k.bls, metadata=k.metadata))
                else:
                    # Not an offender, keep the original validator data
                    filtered_validators.append(k)

            gamma.k = GammaK(filtered_validators)

            # 4.2 . Shift entropy
            state.eta = Eta(
                [state.eta[0], state.eta[0], state.eta[1], state.eta[2]]
            )

            # 4.3. Update seal keys for this coming epoch
            # Check if we are jumping before accumulating ticket.py
            valid_jump = pre_tau % EPOCH_LENGTH > TICKET_SUBMISSION_END
            # If we have sufficient ticket.py accumulated,
            # And we are jumping only one epoch,
            # And we are not jumping before TICKET_SUBMISSION_END
            if len(gamma.a) == EPOCH_LENGTH and epoch_jump == 1 and valid_jump:
                # If we have sufficient ticket.py accumulated,
                # use outside-in sequencer and place the ticket in gamma.s
                gamma.s = GammaS(GammaSTickets(Safrole.outside_in(gamma.a)))
            # Else use the fallback mechanism
            else:
                # Else fallback: use bandersnatch keys
                gamma.s = Safrole.arrange_fallback(
                    state.eta[2], state.kappa
                )

                # 4. 4. Update ring root using gamma k
                gamma.z = GammaZ(Safrole.compute_ring_root([k.bandersnatch for k in state.gamma.k]))

            # 4.5. Empty the ticket acc for upcoming epoch
            gamma.a = GammaA([])

        # 2. Accumulate entropy
        # Use entropy coming from vrf output of Hv once we have valid seals generated
        if int.from_bytes(entropy) > 0:
            eta = state.eta
            eta[0] = Hash.blake2b(
                bytes(state.eta[0]) + bytes(entropy)
            )
            state.eta = eta

        state.gamma = gamma
        return state

    @staticmethod
    def ensure_valid_ticket_extrinsics(block: Block):
        """
        Ensures the ticket.py submitted via the extrinsic are valid.
        """
        Safrole.ensure_tickets_order(block.extrinsic.tickets)
        for ticket in block.extrinsic.tickets:
            Safrole.ensure_valid_vrf(ticket)
            Safrole.ensure_valid_attempt(ticket)
        Safrole.ensure_valid_tickets_count_before_epoch_end(block)
        

    @staticmethod
    def ensure_tickets_order(tickets: TicketsExtrinsic):
        """
        Ensures the ticket.py submitted via the extrinsic must already have been placed in order of their implied identifier.
        https://graypaper.fluffylabs.dev/#/5b732de/0fc7000fc800
        """

        def sort_fn(ticket: TicketEnvelope) -> int:
            # Take VRF output of the signature and sort by it
            return int.from_bytes(Safrole.vrf_output(ticket.signature))

        tickets_sorted = tickets.copy()
        tickets_sorted.sort(key=sort_fn)
        if tickets_sorted != tickets:
            raise SafroleError(
                SafroleErrorCode.BAD_TICKET_ORDER,
                "Tickets are not in sorted order by VRF output",
            )
    # Custom for equ 6.30 check
    
    # Process the ticket.py before TICKET_SUBMISSION_END of the epoch
    @staticmethod
    def ensure_valid_tickets_count_before_epoch_end(block: Block):
        if len(block.extrinsic.tickets) > MAX_TICKETS_PER_EXTRINSIC:
            raise SafroleError(
                SafroleErrorCode.BAD_TICKET_COUNT,
                f"Tickets count {len(block.extrinsic.tickets)} is invalid",
            )

    @staticmethod
    def ensure_valid_vrf(ticket: TicketEnvelope):
        """
        Signature must be valid Ring-VRF proof
        """
        if not Safrole.verify_vrf(ticket.attempt, ticket.signature):
            raise SafroleError(
                SafroleErrorCode.BAD_TICKET_PROOF,
                f"Ticket {ticket} VRF Proof is invalid",
            )

    @staticmethod
    def ensure_valid_attempt(ticket: TicketEnvelope):
        """
        Entry index should be a natural number less than N
        https://graypaper.fluffylabs.dev/#/5b732de/0f22000f2400
        """
        if 0 <= ticket.attempt > TICKET_ENTRIES_PER_VALIDATOR:
            raise SafroleError(
                SafroleErrorCode.BAD_TICKET_ATTEMPT,
                f"Ticket attempt {ticket.attempt} is invalid",
            )

    @staticmethod
    def arrange_fallback(entropy: Bytes, validators: Kappa) -> GammaS:
        """
        This function is to be called in case the ticketing system fails to accumulate valid
        tickeys.
        https://graypaper.fluffylabs.dev/#/68eaa1f/0edf020edf02?v=0.6.4
        Args:
            Etn`2 - Upcoming eta2 or current eta1
            Kappa - List of current validators
        Returns:
            GammaSFallback - Set of Bandersnatch keys
        """
        # Loop through epoch size
        fallback = []
        for i in range(EPOCH_LENGTH):
            # Add entropy to encoded4(i)
            hashed = Hash.blake2b(bytes(entropy) + U32(i).encode())
            index, _ = U32.decode_from(bytes(Bytes(hashed[:4])))
            fallback.append(validators[int(index) % len(validators)].bandersnatch)
        return GammaS(GammaSFallback(fallback))
    
    @staticmethod
    def outside_in(values: list) -> list:
        """
        Returns the outside-in sequenced list of values
        https://graypaper.fluffylabs.dev/#/68eaa1f/0ea8020ebb02?v=0.6.4
        """
        return values[::2] + values[1::2][::-1]

    @staticmethod
    def get_tickets_marker(state: Sigma, slot: U64) -> Option[TicketsMark]:
        """
        Returns the ticket.py markers for the given state
        https://graypaper.fluffylabs.dev/#/68eaa1f/0e82030e8203?v=0.6.4
        - Ensure we have exact EPOCH_LENGTH ticket.py accumulated
        - Ticket collection phase is just getting over (m < TICKET_SUBMISSION_END <= m')
        - We have to be in the same epoch
        """
        if (
            (len(state.gamma.a) == EPOCH_LENGTH) and 
            (state.tau % EPOCH_LENGTH > TICKET_SUBMISSION_END and TICKET_SUBMISSION_END <= slot % EPOCH_LENGTH) and
            (slot // EPOCH_LENGTH == state.tau // EPOCH_LENGTH)
        ):
            return Option[TicketsMark](TicketsMark(Safrole.outside_in(state.gamma.a)))
        else:
            return Option[TicketsMark](Null)

    @staticmethod
    def get_epoch_marker(state: Sigma, slot: U64) -> Option[EpochMark]:
        """
        Returns the epoch marker for the given state
        https://graypaper.fluffylabs.dev/#/68eaa1f/0e3d030e3e03?v=0.6.4
        - Ensure we are moving to a new epoch
        """
        if slot // EPOCH_LENGTH > state.tau // EPOCH_LENGTH:
            return Option[EpochMark](EpochMark(
                entropy=Entropy(state.eta[0]),
                tickets_entropy=Entropy(state.eta[1]),
                validators=ValidatorArray([MinValidatorData(
                    bandersnatch=val.bandersnatch,
                    ed25519=val.ed25519
                ) for val in state.gamma.k])
            ))
        else:
            return Option[EpochMark](Null)
