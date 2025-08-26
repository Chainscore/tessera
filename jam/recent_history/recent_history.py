from copy import deepcopy

from tsrkit_types import TypedVector

from jam.types.state.beta import BlockHistory, Beta
from jam.types.state.sigma import Sigma
from jam.types.block import Block
from jam.types.block import GuaranteesExtrinsic
from jam.types.protocol.crypto import Hash
from jam.merklization import MMRFunctions, BMRFunctions
from jam.types.protocol.merkle import MMR
from jam.types.work import SegmentRootLookup
from jam.utils.constants import RECENT_HISTORY_SIZE
from tsrkit_types.bytes import Bytes


def package(packages: GuaranteesExtrinsic) -> SegmentRootLookup:
    """Transform Guarantees into Dictionary format"""
    package_dict = SegmentRootLookup({})

    for p in packages:
        spec = p.report.package_spec
        package_dict[spec.hash] = spec.exports_root

    return package_dict


class RecentHistory:

    @staticmethod
    def transition(state: Sigma, block: Block) -> Sigma:
        """
        Transition the state's Beta Component and update Recent History.

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/0f0c020f0c02?v=0.7.0

        Args:
            state: State before transition
            block: Block

        Returns:
            State after transition
        """

        beta = state.beta

        # Length Check
        if len(beta.h) > RECENT_HISTORY_SIZE:
            raise ValueError(f"Invalid beta length, must be equal to {RECENT_HISTORY_SIZE}, got {len(beta.h)}")

        mmr_merklizer = MMRFunctions()
        bmr_merklizer = BMRFunctions()

        # Calculate Merkle root of Accumulation Outputs
        accumulate_root = bmr_merklizer.wb_merkle_fn(
            TypedVector[Bytes](sorted([Bytes(comm[0].encode() + comm[1].encode()) for comm in state.theta])),
            Hash.keccak256
        )

        # Append Accumulate root in MMR (β′b)
        beta.b = mmr_merklizer.append_fn(beta.b, accumulate_root, Hash.keccak256)

        # Calculate beefy root
        beefy_root = mmr_merklizer.super_peak(beta.b)

        # Build and append block history in beta
        n = BlockHistory(
            block.header.hash(),
            Bytes[32]([0] * 32),
            beefy_root,
            package(block.extrinsic.guarantees)
        )

        beta.h.append(n)

        # β′h
        beta.h = beta.h[-8:]

        state.beta = Beta(beta)

        # Return State
        return state