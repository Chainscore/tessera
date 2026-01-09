import json
from typing import Self

from jam.block.errors import BlockError, BlockErrorCode
from jam.block.extrinsics.extrinsic import Extrinsic
from jam.types.protocol.ticket import TicketBody
from jam.types.state.gamma import GammaSFallback, GammaSTickets
from jam.utils.constants import EPOCH_LENGTH, X, TICKET_SUBMISSION_END
from tsrkit_types import Option, structure, Null, Bytes
from jam.types import (
    BandersnatchVrfSignature,
    Hash,
    HeaderHash,
    StateRoot,
    OpaqueHash,
    TimeSlot,
    ValidatorIndex, Entropy,
)

from .epoch_mark import EpochMark, EpochMarkData, ValidatorArray, MinValidatorData
from .offenders_mark import OffendersMark
from .tickets_mark import TicketsMark, TicketsMarkData
from dot_ring import IETF_VRF, Bandersnatch

from ...utils.util_fns import outside_in


@structure
class Header:
    """Block header structure."""
    # HP
    parent: HeaderHash
    # HR
    parent_state_root: StateRoot
    # HX
    extrinsic_hash: OpaqueHash
    # HT
    slot: TimeSlot
    # HE
    epoch_mark: EpochMark
    # HT
    tickets_mark: TicketsMark
    # HA
    author_index: ValidatorIndex
    # HV
    entropy_source: BandersnatchVrfSignature
    # HO
    offenders_mark: OffendersMark
    # HS
    seal: BandersnatchVrfSignature

    def __hash__(self) -> int:
        return int.from_bytes(self.hash())

    def encode_unsigned(self) -> bytes:
        return self.encode()[:-96]

    def hash(self) -> HeaderHash:
        return HeaderHash(Hash.blake2b(self.encode()))

    @staticmethod
    def genesis(path="dev-spec.json") -> "Header":
        return Header.decode(bytes.fromhex(json.load(open(path))["genesis_header"]))

    def produce(
        self,
        time_slot: TimeSlot,
        extrinsic: Extrinsic,
        ticket: TicketBody | None,
        state
    ) -> Self | None:
        """
        Produces a child header of current header
        """
        from jam.settings import settings

        header = Header(
            parent=Hash.blake2b(self.encode()),
            parent_state_root=state.root,
            extrinsic_hash=extrinsic.hash(),
            slot=time_slot,
            epoch_mark=EpochMark.produce(state, time_slot),
            tickets_mark=TicketsMark.produce(state, time_slot),
            offenders_mark=OffendersMark.produce(extrinsic.disputes),
            author_index=ValidatorIndex([k.bandersnatch for k in state.kappa].index(settings.bandersnatch_public)),
            entropy_source=BandersnatchVrfSignature(96),
            seal=BandersnatchVrfSignature(96),
        )

        # --- Seal --- #
        # If start of a new epoch, use eta[2], else eta[3]
        eta = state.eta[2] if state.tau // EPOCH_LENGTH != time_slot // EPOCH_LENGTH else state.eta[3]

        # Fallback / Ticket context
        context = (
            X.TICKET.value + eta + bytes([ticket.attempt])
            if ticket
            else X.FALLBACK.value + eta.encode()
        )

        seal_proof = IETF_VRF[Bandersnatch].prove(
            context,
            settings.bandersnatch_private,
            b""
        )
        seal_output = seal_proof.proof_to_hash(seal_proof.output_point)[:32]
        header.entropy_source = BandersnatchVrfSignature(
            IETF_VRF[Bandersnatch].prove(
                X.ENTROPY.value + seal_output, 
                settings.bandersnatch_private,
                b""
            ).to_bytes()
        )
        header.seal = BandersnatchVrfSignature(
            IETF_VRF[Bandersnatch].prove(
                context, 
                settings.bandersnatch_private,
                header.encode_unsigned(),
            ).to_bytes()
        )
        
        return header

    def validate(self, state, pre_state) -> bool:
        """
        Validate a block's header
        1. Extrinsic hash should match hash(block.extrinsics)
        2. Valid Seal + Entropy, matching author
        3. Parent header should exist
        4. Timeslot < curr time
        5. Author index (H_i) <= V
        6. H_e only when epoch transition
        7. H_r == state.root
        """
        from jam.settings import settings

        slot_entry = self.slot % EPOCH_LENGTH
        full_val_set = state.kappa

        # Author check
        if self.author_index >= len(full_val_set):
            raise BlockError(BlockErrorCode.INVALID_AUTHOR)
        author = full_val_set[self.author_index]

        s_vals = state.gamma.s.unwrap()
        entry = s_vals[slot_entry]

        seal = IETF_VRF[Bandersnatch].from_bytes(self.seal)
        seal_output = seal.proof_to_hash(seal.output_point)[:32]
        entropy = IETF_VRF[Bandersnatch].from_bytes(self.entropy_source)

        # Authorized sealer
        if isinstance(s_vals, GammaSFallback):
            if author.bandersnatch != s_vals[slot_entry]:
                raise BlockError(
                    BlockErrorCode.INVALID_AUTHOR, f"Expected: {s_vals[slot_entry].hex()}, Actual: {author.bandersnatch.hex()}",
                )
        else:
            if s_vals[slot_entry].id != seal_output:
                raise BlockError(BlockErrorCode.INVALID_AUTHOR)

        eta = state.eta[3]
        context = (
            X.TICKET.value + eta + bytes([entry.attempt])
            if isinstance(s_vals, GammaSTickets)
            else X.FALLBACK.value + eta.encode()
        )
        # Verify seal
        if not seal.verify(author.bandersnatch, context, self.encode_unsigned()):
            raise BlockError(BlockErrorCode.INVALID_SEAL)

        # Verify entropy
        if not entropy.verify(author.bandersnatch, X.ENTROPY.value + seal_output, b""):
            raise BlockError(BlockErrorCode.INVALID_ENTROPY)

        # State root check
        if self.parent_state_root != state.root:
            raise BlockError(BlockErrorCode.INCORRECT_STATE_ROOT, f"E: {self.parent_state_root.hex()}, A: {state.root.hex()}")

        # Marker checks
        is_new_epoch = (self.slot // EPOCH_LENGTH) > (pre_state.tau // EPOCH_LENGTH)
        # Epoch marker
        if is_new_epoch:
            valid_epoch_mark = EpochMark(
                EpochMarkData(
                    entropy=Entropy(pre_state.eta[0]),
                    tickets_entropy=Entropy(pre_state.eta[1]),
                    validators=ValidatorArray(
                        [
                            MinValidatorData(bandersnatch=val.bandersnatch, ed25519=val.ed25519)
                            for val in state.gamma.p
                        ]
                    ),
                )
            )

            if self.epoch_mark.unwrap() == Null:
                raise BlockError(BlockErrorCode.EPOCH_MARKER_EMPTY)

            if self.epoch_mark != valid_epoch_mark:
                raise BlockError(BlockErrorCode.INVALID_EPOCH_MARK)

        else:
            if self.epoch_mark.unwrap() != Null:
                raise BlockError(BlockErrorCode.EPOCH_MARKER_NOT_EMPTY)

        # If we're in ticket mode
        is_ticket_mode = len(state.gamma.a) >= EPOCH_LENGTH
        is_last_ticket_slot = pre_state.tau % EPOCH_LENGTH < TICKET_SUBMISSION_END and self.slot % EPOCH_LENGTH >= TICKET_SUBMISSION_END

        if is_last_ticket_slot and is_ticket_mode and not is_new_epoch:
            valid_ticket_mark = TicketsMark(TicketsMarkData(outside_in(state.gamma.a)))
            if self.tickets_mark.unwrap() == Null:
                raise BlockError(BlockErrorCode.TICKETS_MARK_EMPTY)
            elif self.tickets_mark != valid_ticket_mark:
                raise BlockError(BlockErrorCode.INVALID_TICKET_MARK)

        if not (is_last_ticket_slot or is_ticket_mode or is_new_epoch) and self.tickets_mark.unwrap() != Null:
            raise BlockError(BlockErrorCode.TICKETS_MARK_NOT_EMPTY)

        # Parent exists
        if settings.main_db.get(self.parent) is None:
            if not self.parent != Bytes[32](32) and self.parent != self.genesis().hash():
                raise BlockError(
                    BlockErrorCode.INVALID_PARENT, f"Parent block not found {self.parent.hex()}"
                )

        return True
