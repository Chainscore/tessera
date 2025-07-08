from typing import List
from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.logging import get_logger
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
    SIGNING_CONTEXTS,
    TICKET_SUBMISSION_END,
    TICKET_ENTRIES_PER_VALIDATOR,
    MAX_TICKETS_PER_EXTRINSIC
)
from jam.types.protocol.crypto import BandersnatchPublic, BandersnatchRingVrfSignature, BandersnatchVrfSignature, BlsPublic, Ed25519Public, Hash, Entropy
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from jam.types.state.gamma import GammaK, GammaSFallback, GammaA, GammaZ
from jam.types.protocol.validators import ValidatorData
from jam.types.protocol.epoch import MinValidatorData, ValidatorArray, EpochMark
from dot_ring.vrf.ring.ring_vrf import RingVrf 
from py_ark_vrf import PublicKey

logger = get_logger("import")


class Safrole:
    @staticmethod
    def generate_ticket() -> TicketEnvelope:
        return TicketEnvelope(
            attempt=U32(0),
            signature=BandersnatchRingVrfSignature(bytes(784)),
        )

    @staticmethod
    def verify_vrf(message: bytes, ring_root: GammaZ, proof: BandersnatchRingVrfSignature) -> bool:
        # return RingVrf.ring_vrf_proof_verify(message, ring_root, proof)
        return True

    @staticmethod
    def compute_ring_root(keys: List[BandersnatchPublic]) -> Bytes[32]:
        # return Bytes[32](RingVrf.construct_ring_root(keys))
        return Bytes[32](PublicKey.get_ring_commitment_bytes(keys))

    @staticmethod
    def vrf_output(signature: BandersnatchRingVrfSignature) -> Bytes[32]:
        return Bytes[32](RingVrf.pedersen_proof_to_hash(signature))

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
        eta = state.eta

        if new_epoch > old_epoch:
            # 4.5. Empty the ticket acc for upcoming epoch
            gamma.a = GammaA([])
        
        # 3. Ticket Accumulation
        ticket_submission_active = (block.header.slot % EPOCH_LENGTH) < TICKET_SUBMISSION_END
        # Process the ticket.py before TICKET_SUBMISSION_END of the epoch, if the epoch is not jumped
        if ticket_submission_active and epoch_jump == 0 and len(block.extrinsic.tickets) > 0:
            # Validate extrinsics
            Safrole.ensure_valid_ticket_extrinsics(block) 
            # Accumulate them in gamma.a
            gamma.a += [
                TicketBody(
                    attempt=ticket.attempt, id=Safrole.vrf_output(ticket.signature)
                )
                for ticket in block.extrinsic.tickets
            ]
            logger.debug(f"Added {len(block.extrinsic.tickets)} tickets")
            gamma.a.sort(key=lambda x: x.id)
            gamma.a = GammaA(gamma.a[:EPOCH_LENGTH])
            # Check for duplicates
            if len(gamma.a) != len(list(set(gamma.a))):
                raise SafroleError(SafroleErrorCode.DUPLICATE_TICKET, "Duplicate tickets are not allowed")
        # We never expect ticket.py after TICKET_SUBMISSION_END
        if not ticket_submission_active and len(block.extrinsic.tickets) > 0:
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
                    filtered_validators.append(ValidatorData(bandersnatch=BandersnatchPublic(32), ed25519=Ed25519Public(32), bls=BlsPublic(144), metadata=Bytes[128](128)))
                else:
                    # Not an offender, keep the original validator data
                    filtered_validators.append(k)

            gamma.k = GammaK(filtered_validators)

            # 4.2 . Shift entropy
            eta = Eta([eta[0], eta[0], eta[1], eta[2]])

            # 4.3. Update seal keys for this coming epoch
            # Check if we are jumping before accumulating ticket.py
            valid_jump = pre_tau % EPOCH_LENGTH > TICKET_SUBMISSION_END
            # If we have sufficient tickets accumulated,
            # And we are jumping only one epoch,
            # And we are not jumping before TICKET_SUBMISSION_END
            if len(state.gamma.a) == EPOCH_LENGTH and epoch_jump == 1 and valid_jump:
                # If we have sufficient ticket.py accumulated,
                # use outside-in sequencer and place the ticket in gamma.s
                gamma.s = GammaS(GammaSTickets(Safrole.outside_in(state.gamma.a)))
            # Else use the fallback mechanism
            else:
                logger.warning("Falling to Fallback mode", tickets_collected=len(state.gamma.a))
                # Else fallback: use bandersnatch keys
                gamma.s = Safrole.arrange_fallback(eta[2], state.kappa)

                # 4. 4. Update ring root using gamma k
                gamma.z = GammaZ(Safrole.compute_ring_root([k.bandersnatch for k in state.gamma.k]))

        for ticket in block.extrinsic.tickets:
            # Signature must be valid Ring-VRF proof
            if not Safrole.verify_vrf(SIGNING_CONTEXTS["ticket_seal"] + state.eta[2] + ticket.attempt.encode(), gamma.z, ticket.signature):
                raise SafroleError(
                    SafroleErrorCode.BAD_TICKET_PROOF,
                    f"Ticket {ticket} VRF Proof is invalid",
                )
        # 2. Accumulate entropy
        # Use entropy coming from vrf output of Hv once we have valid seals generated
        if int.from_bytes(entropy) > 0:
            eta[0] = Hash.blake2b(
                bytes(state.eta[0]) + bytes(entropy)
            )
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
        ret = []
        fwd = values 
        bwd = values[::-1]
        for i in range(len(values)):
            if i % 2:
                ret.append(bwd.pop(0))
            else:
                ret.append(fwd.pop(0))

        return ret

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
