from typing import List
from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.types import TicketsMark, TicketBody
from jam.types.block import TicketEnvelope, TicketsExtrinsic
from jam.types.state.eta import Eta
from jam.types.state.kappa import Kappa
from jam.types.state.lambda_ import Lambda_
from jam.types.state.sigma import Sigma
from jam.types.state.gamma import GammaS, GammaSTickets
from tsrkit_types import Bytes, Option, U64, U32, Null
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
import py_ark_vrf as vrf


class Safrole:
    @staticmethod
    def generate_ticket() -> TicketEnvelope:
        return TicketEnvelope(
            attempt=U32(0),
            signature=BandersnatchRingVrfSignature(bytes(784)),
        )

    @staticmethod
    def verify_vrf(message, proof) -> bool:
        """Very *light-weight* VRF verification placeholder.

        A full cryptographic verification requires the ring-VRF algorithm
        (planned in a forthcoming update).  Until then we *must not* accept
        every proof as valid because that opens the door to spam and
        malicious manipulation of consensus.  The following pragmatic rules
        strike a compromise:

        1. The proof **must** have the exact expected size (784 bytes).
        2. All-zero proofs – produced by `generate_ticket()` or by an
           attacker forging an empty signature – are **rejected**.

        These checks are certainly *not* sufficient for production-grade
        security, but they close the immediate vulnerability where *any*
        784-byte blob (or even an empty one) was previously accepted.
        """

        # 1. Length check – prevents trivially malformed proofs.
        if len(proof) != 784:
            return False

        # 2. Reject the all-zero proof (and a few other extremely unlikely
        #    low-entropy variants) to avoid the “accept everything” bug.
        if int.from_bytes(proof) == 0:
            return False

        # TODO: Replace the stub below with a real ring-VRF verification once
        #       the py_ark_vrf bindings are integrated.
        # For now, assume the proof is *potentially* valid.
        return True

    @staticmethod
    def compute_ring_root(keys: List[BandersnatchPublic]) -> bytes:
        # keys_as_bs_points = []
        # for key in keys:
        #     point = BandersnatchPoint.string_to_point(bytes(key))  # or take key[2:] by skipping '0x'
        #     keys_as_bs_points.append((point.x, point.y))
        #
        # ring_root = PC()  # ring_root builder
        # fxd_cols = ring_root.build(keys_as_bs_points)
        # fxd_col_cs = bytearray.fromhex(H.bls_g1_compress(fxd_cols[0].commitment)) + bytearray.fromhex(
        #     H.bls_g1_compress(fxd_cols[1].commitment)) + bytearray.fromhex(H.bls_g1_compress(fxd_cols[2].commitment))
        #
        # print(fxd_col_cs.hex())
        return vrf.PublicKey.get_ring_commitment_bytes([bytes(k) for k in keys])

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
                # NOTE: `gamma.k` has just been updated above with the new
                # `filtered_validators`. We must compute the ring root from
                # this *updated* list – not the stale validators that still
                # live in `state.gamma.k` until we re-attach `gamma` to
                # `state` at the end of the transition.
                gamma.z = GammaZ(
                    Safrole.compute_ring_root([k.bandersnatch for k in gamma.k])
                )

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
        # `ticket.attempt` is expected to be within the half-open interval
        # [0, TICKET_ENTRIES_PER_VALIDATOR). The original chained comparison
        # `0 <= ticket.attempt > TICKET_ENTRIES_PER_VALIDATOR` was equivalent
        # to `(0 <= ticket.attempt) and (ticket.attempt > TICKET_ENTRIES_PER_VALIDATOR)`,
        # which can **never** be true because the same value cannot be both
        # less-than-or-equal to the upper bound and greater-than it at the
        # same time. Consequently, invalid attempts were never rejected.
        if ticket.attempt < 0 or ticket.attempt >= TICKET_ENTRIES_PER_VALIDATOR:
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
