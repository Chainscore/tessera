import math

from typing import List, TYPE_CHECKING

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from jam.storage.da.mappings import PackageStatusMap
from jam.types import HeaderHash
from jam.utils.task_utils import create_safe_task
from tsrkit_types import Null, String, Option

from jam.block import Block
from jam.block.extrinsics.assurances import AvailAssurance, AvailBitField

from jam.state.transitions.assurances.errors import AssurancesError, AssurancesErrorCode

from jam.types.state.rho import OptionalWorkReportState
from jam.types.state.sigma import Sigma
from jam.types.protocol.crypto import Ed25519Public, Ed25519Signature, Hash, OpaqueHash
from jam.types.work import WorkReports
from jam.utils.constants import (
    X,
    UNAVAILABLE_WORK_EXPIRY,
    VALIDATOR_COUNT,
)


class Assurances:
    """State transition function for the processing of Assurances."""

    @staticmethod
    def transition(pre_state: Sigma, state: Sigma, block: Block) -> (Sigma, List):
        """
        Process the assurances extrinsic.

        Args:
            state: The current state of the chain.
            block: The block to process.

        Returns:
            The new state of the chain.
        """
        settings = state.settings

        # rho_dagger
        rho = state.rho
        kappa = pre_state.kappa

        # Get the assurances from the extrinsic
        assurances = block.extrinsic.assurances

        # Ensure the validator indexes are valid
        Assurances.ensure_validators_valid(assurances)

        # 4. Check if we have supermajority, remove pending report if we do
        core_assurances = [0] * len(rho)

        for assurance in assurances:
            # 1. Ensure the assurance anchor matches the block parent
            if assurance.anchor != block.header.parent:
                raise AssurancesError(
                    AssurancesErrorCode.BAD_ATTESTATION_PARENT,
                    f"Assurance anchor {assurance.anchor} does not match block parent {block.header.parent}",
                )

            # 3. Ensure the assurance signatures are valid
            Assurances.ensure_valid_signature(
                kappa[assurance.validator_index].ed25519,
                assurance.signature,
                assurance.bitfield,
                block.header.parent,
            )

            # Update core assurances
            for i in range(len(assurance.bitfield)):
                if assurance.bitfield[i]:
                    if rho[i].unwrap() == Null:
                        raise AssurancesError(
                            AssurancesErrorCode.CORE_NOT_ENGAGED,
                            f"Pending work report {i} not found",
                        )
                    core_assurances[i] += 1

        # 2. Ensure the assurances are ordered and unique
        Assurances.ensure_assurances_order(assurances)
        Assurances.ensure_assurances_unique(assurances)

        wp_da = PackageStatusMap(settings.d3l)

        # If we have supermajority - add them to newly available WRs list
        newly_avail_reports = WorkReports([])
        # Or if we have any stale pending WRs
        # Clear them
        super_majority = math.floor(2 * VALIDATOR_COUNT / 3)
        for i in range(len(rho)):
            rep = rho[i].unwrap()
            if rep == Null:
                continue
            else:
                if core_assurances[i] > super_majority:
                    newly_avail_reports.append(rep.report)
                    rho[i] = OptionalWorkReportState(Null)

                    wp_hash = rep.report.package_spec.hash

                    # status and reported in cannot be null??
                    status = wp_da.get(wp_hash)
                    assert status.status == String("REPORTED")
                    reported_in = status.reported_in.unwrap()
                    reported_block = Block.load(reported_in, settings.main_db)

                    # Publishes updates for work package
                    val = {
                        "Ready": {
                            "reported_in": {
                                "header_hash": reported_in,
                                "slot": int(reported_block.header.slot)
                            },
                            "core": int(rep.report.core_index),
                            "report_hash": rep.report.hash(),
                            "ready_in": {
                                "slot": int(block.header.slot),
                                "header_hash": block.header.hash()
                            }
                        }
                    }
                    # TODO: Handle this properly
                    if hasattr(state, "publisher"):
                        create_safe_task(
                            state.publisher.publish_work_package_status(wp_hash, rep.report.context.anchor, val)
                        )

                    status.status = String("READY")
                    status.ready_in = Option[HeaderHash](block.header.hash())


                    wp_da.put(wp_hash, status)

                if (
                    core_assurances[i] > super_majority
                    or block.header.slot
                    >= rep.timeout + UNAVAILABLE_WORK_EXPIRY
                ):
                    rho[i] = OptionalWorkReportState(Null)

                    if core_assurances[i] <= super_majority:
                        wp_hash = rep.report.package_spec.hash

                        # status and reported in cannot be null??
                        status = wp_da.get(wp_hash)

                        status.status = String("FAILED")
                        status.err = String("Not enough assurances available in time.")

                        # Publishes updates for work package
                        val = {
                            "Failed": "Not enough assurances available in time"
                        }
                        print("FAIL READY WP STATUS SUB",  block.header.hash().hex(), val)
                        # TODO: HANDLE THIS PROPERLY
                        if hasattr(state, "publisher"):
                            create_safe_task(
                                state.publisher.publish_work_package_status(wp_hash, rep.report.context.anchor, val)
                            )
                        # asyncio.create_task(
                        #     subscribe_work_package_status(wp_hash, rep.report.context.anchor, val))

                        wp_da.put(wp_hash, status)


        state.rho = rho

        return state, newly_avail_reports

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
                X.AVAILABLE.value + bytes(Hash.blake2b(bytes(parent) + bitfield.encode())),
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
