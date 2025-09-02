from typing import List

from jam.types.protocol.ticket import TicketBody
from .errors import SafroleError, SafroleErrorCode
from jam.logging import get_logger
from jam.block import TicketEnvelope, TicketsExtrinsic
from jam.types.state.eta import Eta
from jam.types.state.kappa import Kappa
from jam.types.state.lambda_ import Lambda_
from jam.types.state.sigma import Sigma
from jam.types.state.gamma import GammaS, GammaSTickets
from jam.utils.util_fns import outside_in
from tsrkit_types import Bytes, U64, U32, Null
from jam.block import Block
from jam.utils.constants import (
    EPOCH_LENGTH,
    X,
    TICKET_SUBMISSION_END,
    TICKET_ENTRIES_PER_VALIDATOR,
    MAX_TICKETS_PER_EXTRINSIC,
)
from jam.types.protocol.crypto import (
    BandersnatchPublic,
    BandersnatchRingVrfSignature,
    BlsPublic,
    Ed25519Public,
    Hash,
    OpaqueHash,
)
from jam.types.state.gamma import GammaP, GammaSFallback, GammaA, GammaZ
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
# from dot_ring.vrf.ring.ring_vrf import RingVrf
from py_ark_vrf import verify_ring, get_ring_root, vrf_output

logger = get_logger("import")


class Safrole:
    @staticmethod
    def verify_vrf(
        message: bytes, ring_root: bytes, gamma_p: list[bytes], proof: BandersnatchRingVrfSignature
    ) -> bool:
        # return RingVrf.ring_vrf_proof_verify(message, ring_root, proof)
        return verify_ring(message, proof, gamma_p, b"")  # Input Data  # Proof  # Ring  # AD

    @staticmethod
    def compute_ring_root(keys: List[BandersnatchPublic]) -> GammaZ:
        # return Bytes[32](RingVrf.construct_ring_root(keys))
        # return Bytes[32](PublicKey.get_ring_commitment_bytes(keys))
        return GammaZ(get_ring_root(keys))

    @staticmethod
    def get_vrf_output(signature: BandersnatchRingVrfSignature) -> OpaqueHash:
        # return Bytes[32](RingVrf.pedersen_proof_to_hash(signature))
        return OpaqueHash(vrf_output(signature)[:32])

    @staticmethod
    def transition(pre_state: Sigma, state: Sigma, block: Block, entropy: OpaqueHash) -> Sigma:
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
        eta = state.eta

        if new_epoch > old_epoch:
            # 4.5. Empty the ticket acc for upcoming epoch
            gamma.a = GammaA([])

        # 3. Ticket Accumulation
        ticket_submission_active = (block.header.slot % EPOCH_LENGTH) < TICKET_SUBMISSION_END
        # Process the tickets before TICKET_SUBMISSION_END of the epoch, if the epoch is not jumped
        # TEST: We removed jump == 0 here bc we also allow tickets to be introduced in an epoch's new slot
        if ticket_submission_active and len(block.extrinsic.tickets) > 0:
            # Validate extrinsics
            Safrole.ensure_valid_ticket_extrinsics(block)
            # Accumulate them in gamma.a
            gamma.a += [
                TicketBody(attempt=ticket.attempt, id=Safrole.get_vrf_output(ticket.signature))
                for ticket in block.extrinsic.tickets
            ]
            gamma.a.sort(key=lambda x: x.id)
            gamma.a = GammaA(gamma.a[:EPOCH_LENGTH])
            # Check for duplicates
            if len(gamma.a) != len(list(set(gamma.a))):
                raise SafroleError(
                    SafroleErrorCode.DUPLICATE_TICKET,
                    "Duplicate tickets are not allowed",
                )

        # We never expect tickets after TICKET_SUBMISSION_END
        if not ticket_submission_active and len(block.extrinsic.tickets) > 0:
            raise SafroleError(
                SafroleErrorCode.UNEXPECTED_TICKET,
                "Tickets are not allowed after TICKET_SUBMISSION_END",
            )

        # 4. Epoch transition
        if new_epoch > old_epoch:
            # 4.1. Rotate validators
            state.lambda_ = Lambda_(state.kappa)
            state.kappa = Kappa(gamma.p)
            filtered_validators = []

            for k in state.iota:
                if k.ed25519 in state.psi.offenders:
                    # Offender found, replace with default ValidatorData
                    filtered_validators.append(
                        ValidatorData(
                            bandersnatch=BandersnatchPublic(32),
                            ed25519=Ed25519Public(32),
                            bls=BlsPublic(144),
                            metadata=ValidatorMetadata.decode(bytes(128)),
                        )
                    )
                else:
                    # Not an offender, keep the original validator data
                    filtered_validators.append(k)

            gamma.p = GammaP(filtered_validators)

            # 4.2 . Shift entropy
            eta = Eta([eta[0], eta[0], eta[1], eta[2]])

            # 4.3. Update seal keys for this coming epoch
            # Check if we are jumping before accumulating ticket.py
            valid_jump = pre_tau % EPOCH_LENGTH > TICKET_SUBMISSION_END
            # If we have sufficient tickets accumulated,
            # And we are jumping only one epoch,
            # And we are not jumping before TICKET_SUBMISSION_END
            if len(pre_state.gamma.a) == EPOCH_LENGTH and epoch_jump == 1 and valid_jump:
                # If we have sufficient tickets accumulated,
                # use outside-in sequencer and place the ticket in gamma.s
                logger.warning("Safrole ticketing mode", tickets_collected=len(state.gamma.a))
                gamma.s = GammaS(GammaSTickets(outside_in(pre_state.gamma.a)))
            # Else use the fallback mechanism
            else:
                logger.warning("Falling to Fallback mode", tickets_collected=len(state.gamma.a))
                # Else fallback: use bandersnatch keys
                gamma.s = Safrole.arrange_fallback(eta[2], state.kappa)

            # 4. 4. Update ring root using gamma k
            gamma.z = Safrole.compute_ring_root([k.bandersnatch for k in gamma.p])

        for ticket in block.extrinsic.tickets:
            # Signature must be valid Ring-VRF proof
            if not Safrole.verify_vrf(
                X.TICKET.value + eta[2] + bytes([ticket.attempt]),
                gamma.z,
                [k.bandersnatch for k in gamma.p],
                ticket.signature,
            ):
                raise SafroleError(
                    SafroleErrorCode.BAD_TICKET_PROOF,
                    f"Ticket {ticket} VRF Proof is invalid",
                )
        # 2. Accumulate entropy
        # Use entropy coming from vrf output of Hv once we have valid seals generated
        if int.from_bytes(entropy) > 0:
            eta[0] = Hash.blake2b(bytes(state.eta[0]) + bytes(entropy))
            logger.debug("New Eta[0]", eta=eta[0].hex())
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
            Safrole.ensure_valid_attempt(ticket)
        Safrole.ensure_valid_tickets_count_before_epoch_end(block)

    @staticmethod
    def ensure_tickets_order(tickets: TicketsExtrinsic):
        """
        Ensures the tickets submitted via the extrinsic must already have been placed in order of their implied identifier.
        https://graypaper.fluffylabs.dev/#/5b732de/0fc7000fc800
        """

        def sort_fn(ticket: TicketEnvelope) -> int:
            # Take VRF output of the signature and sort by it
            return int.from_bytes(Safrole.get_vrf_output(ticket.signature))

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
    def ensure_valid_attempt(ticket: TicketEnvelope):
        """
        Entry index should be a natural number less than N
        https://graypaper.fluffylabs.dev/#/5b732de/0f22000f2400
        """
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
            val_key = validators[int(index) % len(validators)].bandersnatch
            fallback.append(val_key)
        return GammaS(GammaSFallback(fallback))
