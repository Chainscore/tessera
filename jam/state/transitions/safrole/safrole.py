from copy import copy
from functools import lru_cache

from jam.models.protocol.ticket import TicketBody
from .errors import SafroleError, SafroleErrorCode
from jam.log_setup import logger
from jam.block import TicketEnvelope
from jam.models.state.eta import Eta
from jam.models.state.kappa import Kappa
from jam.models.state.lambda_ import Lambda_
from jam.models.state.sigma import Sigma
from jam.models.state.gamma import GammaS, GammaSTickets
from jam.utils.util_fns import outside_in
from tsrkit_types import Bytes, U32
from jam.block import Block
from jam.utils.constants import (
    EPOCH_LENGTH,
    X,
    TICKET_SUBMISSION_END,
    TICKET_ENTRIES_PER_VALIDATOR,
    MAX_TICKETS_PER_EXTRINSIC,
)
from jam.models.protocol.crypto import (
    BandersnatchPublic,
    BlsPublic,
    Ed25519Public,
    Hash,
    OpaqueHash,
)
from jam.models.state.gamma import GammaP, GammaSFallback, GammaA, GammaZ
from jam.models.protocol.validators import ValidatorData, ValidatorMetadata
from dot_ring import Bandersnatch, Ring, RingRoot, RingVRF


class Safrole:
    @staticmethod
    def build_ring(keys: list[bytes]) -> Ring:
        return Safrole._build_ring(tuple(bytes(k) for k in keys))

    @staticmethod
    @lru_cache(maxsize=16)
    def _build_ring(keys: tuple[bytes, ...]) -> Ring:
        return Ring(list(keys))

    @staticmethod
    def build_ring_root(ring: Ring) -> RingRoot:
        return RingRoot.from_ring(ring)

    @staticmethod
    @lru_cache(maxsize=16)
    def ring_root_from_bytes(data: bytes) -> RingRoot:
        return RingRoot.from_bytes(data)

    @staticmethod
    def compute_ring_root(keys: list[BandersnatchPublic]) -> GammaZ:
        ring = Safrole.build_ring(keys)
        ring_root = Safrole.build_ring_root(ring)
        return GammaZ(ring_root.to_bytes())

    @staticmethod
    def transition(pre_state: Sigma, state: Sigma, block: Block, entropy: OpaqueHash) -> Sigma:
        pre_tau = pre_state.tau
        # 1. Timekeeping
        if block.header.slot > pre_state.tau:
            state.tau = block.header.slot
        elif pre_state.tau > 0:
            raise SafroleError(
                SafroleErrorCode.BAD_SLOT,
                f"Slot {block.header.slot} is less than current tau {state.tau}",
            )

        old_epoch = int(pre_tau) // EPOCH_LENGTH
        new_epoch = int(block.header.slot) // EPOCH_LENGTH
        epoch_jump = new_epoch - old_epoch

        gamma = copy(state.gamma)
        eta = pre_state.eta

        if new_epoch > old_epoch:
            # 4.5. Empty the ticket acc for upcoming epoch
            gamma.a = GammaA([])

        tickets = block.extrinsic.tickets
        count = len(tickets)

        # 3. Ticket Accumulation
        ticket_submission_active = (block.header.slot % EPOCH_LENGTH) < TICKET_SUBMISSION_END
        # Process the tickets before TICKET_SUBMISSION_END of the epoch, if the epoch is not jumped
        # TEST: We removed jump == 0 here bc we also allow tickets to be introduced in an epoch's new slot
        if ticket_submission_active and (count > 0):
            # Validate extrinsics
            Safrole.ensure_valid_tickets_count_before_epoch_end(block)

            vrf_ids = []
            parsed_vrfs = []
            for i, t in enumerate(tickets):
                Safrole.ensure_valid_attempt(t)
                try:
                    ring_proof = RingVRF[Bandersnatch].from_bytes(bytes(t.signature), skip_pedersen=False)
                    vrf_op = OpaqueHash(ring_proof.proof_to_hash(ring_proof.pedersen_proof.output_point)[:32])
                except Exception as e:
                    raise SafroleError(
                        SafroleErrorCode.BAD_TICKET_PROOF,
                        f"Ticket {t.attempt} VRF Proof is invalid",
                    )
                vrf_ids.append(vrf_op)
                parsed_vrfs.append(ring_proof)
                if i > 0:
                    Safrole.ensure_tickets_order(vrf_ids[i-1], vrf_op)

                # Accumulate them in gamma.a
                gamma.a.append(TicketBody(attempt=t.attempt, id=vrf_op))

            vrf_ids.clear()
            gamma.a.sort(key=lambda x: x.id)

            # Check duplicates before truncating.
            if len(gamma.a) != len(set(gamma.a)):
                raise SafroleError(
                    SafroleErrorCode.DUPLICATE_TICKET,
                    "Duplicate tickets are not allowed",
                )

            gamma.a = GammaA(gamma.a[:EPOCH_LENGTH])

        # We never expect tickets after TICKET_SUBMISSION_END
        if not ticket_submission_active and count > 0:
            raise SafroleError(
                SafroleErrorCode.UNEXPECTED_TICKET,
                "Tickets are not allowed after TICKET_SUBMISSION_END",
            )

        ring = None

        # 4. Epoch transition
        if new_epoch > old_epoch:
            # 4.1. Rotate validators
            state.lambda_ = Lambda_(pre_state.kappa)
            state.kappa = Kappa(gamma.p)
            filtered_validators = []

            for k in pre_state.iota:
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
            valid_jump = pre_tau % EPOCH_LENGTH >= TICKET_SUBMISSION_END
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
                logger.warning("Fallback mode", t=len(pre_state.gamma.a))
                # Else fallback: use bandersnatch keys
                gamma.s = Safrole.arrange_fallback(eta[2], state.kappa)

            # 4.4. Update ring root when the epoch transition changes gamma p.
            if gamma.p != pre_state.gamma.p:
                pubkeys = [bytes(k.bandersnatch) for k in gamma.p]
                ring = Safrole.build_ring(pubkeys)
                ring_root = Safrole.build_ring_root(ring)
                gamma.z = GammaZ(ring_root.to_bytes())

        # Get ring root for ticket validation (may be from state if no epoch transition)
        if ring is None:
            pubkeys = [bytes(k.bandersnatch) for k in gamma.p]
            ring = Safrole.build_ring(pubkeys)
        ring_root = Safrole.ring_root_from_bytes(bytes(gamma.z))

        parsed_vrfs = parsed_vrfs if ticket_submission_active and count > 0 else []

        for i, ticket in enumerate(tickets):
            try:
                vrf = parsed_vrfs[i] if parsed_vrfs else RingVRF[Bandersnatch].from_bytes(ticket.signature)
                if not vrf.verify(
                    X.TICKET.value + eta[2] + bytes([ticket.attempt]),
                    b"",
                    ring,
                    ring_root,
                ):
                    raise SafroleError(
                        SafroleErrorCode.BAD_TICKET_PROOF,
                        f"Ticket {ticket.attempt} VRF Proof is invalid",
                    )
            except Exception:
                raise SafroleError(
                    SafroleErrorCode.BAD_TICKET_PROOF,
                    f"Ticket {ticket.attempt} VRF Proof is invalid",
                )

        # 2. Accumulate entropy
        # Use entropy coming from vrf output of Hv once we have valid seals generated
        if int.from_bytes(entropy) > 0:
            eta[0] = Hash.blake2b(bytes(eta[0]) + bytes(entropy))
        state.eta = eta

        state.gamma = gamma
        return state

    @staticmethod
    def ensure_tickets_order(vrf_op_a: bytes, vrf_op_b: bytes):
        """
        Ensures the tickets submitted via the extrinsic must already have been placed in order of their implied identifier.
        https://graypaper.fluffylabs.dev/#/5b732de/0fc7000fc800
        """

        # Raise Error if any 2 consecutive tickets are wrongly ordered
        if vrf_op_a > vrf_op_b:
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
        entropy_bytes = bytes(entropy)
        for i in range(EPOCH_LENGTH):
            # Add entropy to encoded4(i)
            hashed = Hash.blake2b(entropy_bytes + U32(i).encode())
            index, _ = U32.decode_from(hashed[:4])
            val_key = validators[int(index) % len(validators)].bandersnatch
            fallback.append(val_key)
        return GammaS(GammaSFallback(fallback))
