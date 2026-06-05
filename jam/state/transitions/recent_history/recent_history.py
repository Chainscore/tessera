from jam.models import OpaqueHash, HeaderHash
from jam.models.protocol.core import SegmentRoot, WorkPackageHash
from jam.models.state.beta import BlockHistory, Beta, BetaHistory
from jam.models.state.sigma import Sigma
from jam.block import Block
from jam.block import GuaranteesExtrinsic
from jam.models.protocol.crypto import Hash
from jam.utils.merkle import MMRFunctions, BMRFunctions
from jam.models.protocol.merkle import MMR
from jam.models.work import SegmentRootLookup
from jam.utils.constants import RECENT_HISTORY_SIZE
from tsrkit_types.bytes import Bytes


def package(packages: GuaranteesExtrinsic) -> SegmentRootLookup:
    """Transform Guarantees into Dictionary format"""
    package_dict = SegmentRootLookup({})

    for p in packages:
        spec = p.report.package_spec
        package_dict[WorkPackageHash(spec.hash)] = SegmentRoot(spec.exports_root)

    return package_dict


class RecentHistory:
    @staticmethod
    def transition(
        pre_state: Sigma, state: Sigma, block: Block, acc_root: OpaqueHash, header_hash: HeaderHash
    ) -> Sigma:
        """
        Transition the state's Beta Component and update Recent History.

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/0f0c020f0c02?v=0.7.0

        Args:
            state: State before transition
            block: Block

        Returns:
            State after transition
        """

        beta_dagger = state.beta
        # This is done again for passing test vectors
        if len(beta_dagger.h):
            beta_dagger.h[-1].state_root = block.header.parent_state_root

        # Length Check
        if len(beta_dagger.h) > RECENT_HISTORY_SIZE:
            raise ValueError(
                f"Invalid beta length, must be equal to {RECENT_HISTORY_SIZE}, got {len(beta_dagger.h)}"
            )

        mmr_merklizer = MMRFunctions()

        # Append Accumulate root in MMR (β′b)
        beta_dagger.b = mmr_merklizer.append_fn(beta_dagger.b, acc_root, Hash.keccak256)

        # Calculate beefy root
        beefy_root = mmr_merklizer.super_peak(beta_dagger.b)

        # Build and append block history in beta
        n = BlockHistory(
            header_hash=header_hash,
            timeslot=block.header.slot,
            state_root=Bytes[32]([0] * 32),
            beefy_root=beefy_root,
            reported=package(block.extrinsic.guarantees),
        )

        beta_dagger.h.append(n)

        # β′h
        beta_dagger.h = BetaHistory(beta_dagger.h[-RECENT_HISTORY_SIZE:])

        state.beta = beta_dagger

        # Return State
        return state
