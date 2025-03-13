import dataclasses
from typing import List
from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.state.components.eta import Eta
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_
from .gamma import GammaS, GammaSTickets
from jam.state.state import State
from jam.types import TicketBody, U32, TicketsExtrinsic, TicketEnvelope
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.block import Block
from jam.utils.constants import (
    EPOCH_LENGTH,
    TICKET_SUBMISSION_END,
    TICKET_ENTRIES_PER_VALIDATOR,
    MAX_TICKETS_PER_EXTRINSIC
)
from jam.types.protocol.crypto import BandersnatchPublic, BandersnatchVrfSignature, Hash
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from jam.consensus.safrole.gamma import GammaK, GammaSFallback, GammaA
from jam.types.protocol.validators import ValidatorData

class Safrole:
    @staticmethod
    def verify_vrf(message, proof) -> bool:
        # TODO: Implement VRF verification after VRF module is added
        return True

    @staticmethod
    def compute_ring_root(keys: List[BandersnatchPublic]) -> bytes:
        # TODO - Implementation of KZG_commitment(⟦HB⟧) once the module is added
        sorted_keys = sorted(keys)
        data = b""
        for key in sorted_keys:
            data = data + bytes(key)
        return data[:72]

    @staticmethod
    def vrf_output(signature: BandersnatchVrfSignature) -> ByteArray32:
        # TODO - Use Ring VRF class once it's implemented
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
        return ByteArray32(vrf.proof_to_hash(BandersnatchPoint.string_to_point(bytes(signature)[:32]))[:32])

    @staticmethod
    def transition(pre_state: State, block: Block) -> State:
        new_state = dataclasses.replace(pre_state)

        # 1. Timekeeping
        if block.header.slot > new_state.tau:
            new_state.tau = block.header.slot
        else:
            raise SafroleError(
                SafroleErrorCode.BAD_SLOT,
                f"Slot {block.header.slot} is less than current tau {new_state.tau}",
            )

        # 3. Ticket Accumulation
        ticket_submission_active = (pre_state.tau % EPOCH_LENGTH) < TICKET_SUBMISSION_END
        # Process the tickets before TICKET_SUBMISSION_END of the epoch
        if ticket_submission_active:
            # Validate extrinsics
            Safrole.ensure_valid_ticket_extrinsics(block)
            # Accumulate them in gamma.a
            new_state.gamma.a += [
                TicketBody(
                    attempt=ticket.attempt, id=Safrole.vrf_output(ticket.signature)
                )
                for ticket in block.extrinsic.tickets
            ]
            new_state.gamma.a.sort(key=lambda x: x.id)
            new_state.gamma.a = new_state.gamma.a[:EPOCH_LENGTH]
            # Remove duplicates
            new_state.gamma.a = GammaA(new_state.gamma.a)
        else:
            Safrole.ensure_valid_tickets_count_after_epoch_end(block)
        # 4. Epoch transition
        old_epoch = int(pre_state.tau) // EPOCH_LENGTH
        new_epoch = int(block.header.slot) // EPOCH_LENGTH
        epoch_jump = new_epoch - old_epoch
        if new_epoch > old_epoch:
            # 4.1. Rotate validators
            new_state.lambda_ = Lambda_(pre_state.kappa.value)
            new_kappa = Kappa(pre_state.gamma.k)
            new_state.kappa = new_kappa
            filtered_validators=[]
            for k in pre_state.iota:
                if k.ed25519 in pre_state.psi.o:
                    # Offender found, replace with default ValidatorData
                    filtered_validators.append(ValidatorData(bandersnatch=ByteArray32(bytes(32)), ed25519=ByteArray32(bytes(32)), bls=k.bls, metadata=k.metadata))
                else:
                    # Not an offender, keep the original validator data
                    filtered_validators.append(k)
            
            new_state.gamma.k = GammaK(filtered_validators)

            # 4.2 . Shift entropy
            new_state.eta = Eta(
                [new_state.eta[0], new_state.eta[0], new_state.eta[1], new_state.eta[2]]
            )

            # 4.3. Update seal keys for this coming epoch
            if len(new_state.gamma.a) == EPOCH_LENGTH and epoch_jump == 1 and not ticket_submission_active:
                # If we have sufficient tickets accumulated,
                # use outside-in sequencer and place the ticket in gamma.s
                acc_tickets = []
                for i in range(len(new_state.gamma.a) // 2):
                    acc_tickets.append(new_state.gamma.a[i])
                    acc_tickets.append(new_state.gamma.a[len(new_state.gamma.a) - 1 - i])
                new_state.gamma.s = GammaS(GammaSTickets(acc_tickets))
            
            else:
                # Else fallback: use bandersnatch keys
                new_state.gamma.s = Safrole.arrange_fallback(
                    new_state.eta[2], new_state.kappa
                )

            # 4. 4. Update ring root
            new_state.gamma.z = Safrole.compute_ring_root(
                [k.bandersnatch for k in new_state.kappa]
            ).hex()

            # 4.5. Empty the ticket acc for upcoming epoch
            new_state.gamma.a = GammaA([])

        # 2. Accumulate entropy
        if block.header.epoch_mark:
            new_state.eta[0] = Hash.blake2b(
                bytes(new_state.eta[0]) + (bytes(block.header.epoch_mark.get_value().entropy))
            )

        return new_state

    @staticmethod
    def ensure_valid_ticket_extrinsics(block: Block):
        """
        Ensures the tickets submitted via the extrinsic are valid.
        """
        Safrole.ensure_tickets_order(block.extrinsic.tickets)
        for ticket in block.extrinsic.tickets:
            Safrole.ensure_valid_vrf(ticket)
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
            return Safrole.vrf_output(ticket.signature).to_int()

        tickets_sorted = tickets.copy()
        tickets_sorted.sort(key=sort_fn)
        if tickets_sorted != tickets:
            raise SafroleError(
                SafroleErrorCode.BAD_TICKET_ORDER,
                "Tickets are not in sorted order by VRF output",
            )
    # Custom for equ 6.30 check
    
    # Process the tickets before TICKET_SUBMISSION_END of the epoch
    @staticmethod
    def ensure_valid_tickets_count_before_epoch_end(block: Block):
        if len(block.extrinsic.tickets) > MAX_TICKETS_PER_EXTRINSIC:
            raise SafroleError(
                SafroleErrorCode.BAD_TICKET_COUNT,
                f"Tickets count {len(block.extrinsic.tickets)} is invalid",
            )
    # Process the tickets after TICKET_SUBMISSION_END of the epoch
    @staticmethod
    def ensure_valid_tickets_count_after_epoch_end(block: Block):
        if len(block.extrinsic.tickets) > 0:
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
        if ticket.attempt >= TICKET_ENTRIES_PER_VALIDATOR:
            raise SafroleError(
                SafroleErrorCode.BAD_TICKET_ATTEMPT,
                f"Ticket attempt {ticket.attempt} is invalid",
            )

    @staticmethod
    def arrange_fallback(entropy: Bytes, validators: Kappa) -> GammaS:
        """
        This function is to be called in case the ticketing system fails to accumulate valid
        tickeys.
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
