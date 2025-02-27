from jam.state.state import State
from jam.state.components.beta import BlockHistory, PackageDict
from jam.types import ByteArray32
from jam.types.block import Block
from jam.types.extrinsics import GuaranteesExtrinsic
from jam.types.protocol.crypto import Hash
from jam.merklization import MMRFunctions, MMR
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import RECENT_HISTORY_SIZE
from jam.types.protocol.core import WorkPackageHash, SegmentRoot


import dataclasses

def package(packages: GuaranteesExtrinsic) -> PackageDict:
    """Transform Guarantees into Dictionary format"""
    package_dict:PackageDict[WorkPackageHash, SegmentRoot] = PackageDict()

    for p in packages:
        a= p.report.segment_root_lookup
        for c in a:
            b = c.work_package_hash
            d = c.segment_tree_root
            package_dict[b]=d

    return package_dict

class RecentHistory:

    @staticmethod
    def transition(pre_state: State, block: Block, accumulate_root: OpaqueHash) -> State:
        """
        Transition the state's Beta Component and update Recent History.
        Includes 3 steps

        Step 1:
            Create a Beta dagger state & Update State Root of last block in History
            Defined in eqn 7.2

            β † ≡ β except β † [∣β∣ − 1]s = Hr

        Step 2:
            Create Accumulate Root (Once On Chain) r,
            Append that Root in MMR and get Updated MMR b,
            Get Packages p from guarantees extrinsic

            Add all the values in new History Block n.
            Defined in eqn 7.3

            let r = MB([s ^^ E4(s) ⌢ E(h) ∣ (s, h) ∈ C], HK )
            let b = A(last([[]] ⌢ [xb ∣ x <− β]), r, HK )
            let p = {((gw)s )h ↦ ((gw)s )e ∣ g ∈ EG}
            let n = (p, h: H(H), b, s: H0)

        Step 3:
            Append n into recent history vector and take last 8 blocks in recent history.
            Defined in eqn 7.4

                 ←----- H
            β' ≡ β†  #  n

        Source:
            https://graypaper.fluffylabs.dev/#/5f542d7/0faf010fb001

        Args:
            pre_state: State before transition
            block: Block
            accumulate_root: Calculated Merklization State Root

        Returns:
            State after transition
        """

        # Make a copy of the state
        new_state: State = dataclasses.replace(pre_state)

        # Step 1
        if len(new_state.beta):
            new_state.beta[-1].state_root = block.header.parent_state_root

        # Length Check
        if len(new_state.beta) > RECENT_HISTORY_SIZE:
            raise ValueError("Invalid beta length, must be equal to RECENT_HISTORY_SIZE")

        # Step 2
        last: MMR = MMR([])
        if len(new_state.beta) > 0:
            last = new_state.beta[-1].mmr

        mmr_functions = MMRFunctions()

        n = BlockHistory(
            block.header.parent,
            mmr_functions.append_fn(last, accumulate_root, Hash.keccak256),
            ByteArray32([0] * 32),
            package(block.extrinsic.guarantees)
        )

        # Step 3
        new_state.beta.append(n)
        new_state.beta = new_state.beta[-8:]

        # Return Updated State
        return new_state