import dataclasses
import math
from typing import List, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from jam.assurances.errors import AssurancesError, AssurancesErrorCode
from jam.state.components.rho import OptionalWorkReportState
from jam.state.state import State
from jam.types.base.null import Null
from jam.types.block import Block
from jam.types.extrinsics.assurances import AvailAssurance, AvailBitField
from jam.types.protocol.crypto import Ed25519Public, Ed25519Signature, Hash, OpaqueHash
from jam.types.work.report import WorkReport
from jam.utils.constants import (
    SIGNING_CONTEXTS,
    UNAVAILABLE_WORK_EXPIRY,
    VALIDATOR_COUNT,
)


class Assurances:
    """State transition function for the processing of Assurances."""

    @staticmethod
    def transition(state: State, block: Block) -> Tuple[State, List[WorkReport]]:
        """
        Process the assurances extrinsic.
        
        Args:
            state: The current state of the chain.
            block: The block to process.

        Returns:
            The new state of the chain.
        """
        # Make a copy of the state
        new_state = dataclasses.replace(state)

        # Get the assurances from the extrinsic
        assurances = block.extrinsic.assurances

        # Ensure the validator indexes are valid
        Assurances.ensure_validators_valid(assurances)

        # 4. Check if we have supermajority, remove pending report if we do
        core_assurances = [0] * len(state.rho)

        for assurance in assurances:
            # 1. Ensure the assurance anchor matches the block parent
            if assurance.anchor != block.header.parent:
                raise AssurancesError(
                    AssurancesErrorCode.BAD_ATTESTATION_PARENT,
                    f"Assurance anchor {assurance.anchor} does not match block parent {block.header.parent}",
                )

            # 3. Ensure the assurance signatures are valid
            Assurances.ensure_valid_signature(
                state.kappa[assurance.validator_index].ed25519,
                assurance.signature,
                assurance.bitfield,
                block.header.parent,
            )

            # Update core assurances
            for i in range(len(assurance.bitfield)):
                if state.rho[i].get_value() == Null:
                    raise AssurancesError(
                        AssurancesErrorCode.CORE_NOT_ENGAGED,
                        f"Pending work report {i} not found",
                    )
                if assurance.bitfield[i]:
                    core_assurances[i] += 1

        # 2. Ensure the assurances are ordered and unique
        Assurances.ensure_assurances_order(assurances)
        Assurances.ensure_assurances_unique(assurances)

        # If we have supermajority add them to the available WRS
        available_wrs = []
        super_majority = math.floor(2 * VALIDATOR_COUNT / 3)
        for i in range(len(state.rho)):
            pending_wr = state.rho[i].get_value()
            if pending_wr is not None:
                # If we have supermajority add them to the available WRS & clear them
                if core_assurances[i] > super_majority:
                    available_wrs.append(pending_wr)
                    new_state.rho[i] = OptionalWorkReportState(Null)
                # If we have any stale pending WRs - clear them
                if block.header.slot >= pending_wr.timeout + UNAVAILABLE_WORK_EXPIRY:
                    new_state.rho[i] = OptionalWorkReportState(Null)

        return (new_state, available_wrs)

    @staticmethod
    def ensure_valid_signature(
        public_key: Ed25519Public,
        signature: Ed25519Signature,
        bitfield: AvailBitField,
        parent: OpaqueHash,
    ) -> None:
        """Ensure the signature is valid"""
        try:
            Ed25519PublicKey.from_public_bytes(bytes(public_key)).verify(
                bytes(signature),
                SIGNING_CONTEXTS["available"]
                + bytes(Hash.blake2b(bytes(parent) + bitfield.encode())),
            )
        except InvalidSignature:
            raise AssurancesError(
                AssurancesErrorCode.BAD_SIGNATURE,
                f"Assurance signature {signature} is invalid",
            )

    @staticmethod
    def ensure_validators_valid(assurances: List[AvailAssurance]) -> None:
        """Ensure the validator index is valid"""
        for assurance in assurances:
            if assurance.validator_index >= VALIDATOR_COUNT:
                raise AssurancesError(
                    AssurancesErrorCode.BAD_VALIDATOR_INDEX,
                    f"Validator index {assurance.validator_index} is invalid",
                )

    @staticmethod
    def ensure_assurances_order(assurances: List[AvailAssurance]) -> None:
        """Ensure the assurances are ordered by validator index."""
        expected_assurances = sorted(assurances, key=lambda x: x.validator_index)
        if assurances != expected_assurances:
            raise AssurancesError(
                AssurancesErrorCode.NOT_SORTED_OR_UNIQUE_ASSURERS,
                "Assurances are not ordered by validator index",
            )

    @staticmethod
    def ensure_assurances_unique(assurances: List[AvailAssurance]) -> None:
        """Ensure the assurances are unique using Python's set"""
        if len(assurances) != len(
            set(assurance.validator_index for assurance in assurances)
        ):
            raise AssurancesError(
                AssurancesErrorCode.NOT_SORTED_OR_UNIQUE_ASSURERS,
                "Assurances are not unique by validator index",
            )
