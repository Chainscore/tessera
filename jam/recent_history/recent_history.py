from copy import deepcopy
from jam.types.state.beta import BlockHistory, Beta
from jam.types.state.sigma import Sigma
from jam.types.block import Block
from jam.types.block import GuaranteesExtrinsic
from jam.types.protocol.crypto import Hash
from jam.merklization import MMRFunctions
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
    def transition(state: Sigma, block: Block, accumulate_root = Bytes[32]([0] * 32), header_hash=None) -> Sigma:
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
            state: State before transition
            block: Block
            accumulate_root: Calculated Merklization State Root

        Returns:
            State after transition
        """
        beta = state.beta
        # Step 1
        if len(beta):
            beta[-1].state_root = block.header.parent_state_root

        # Length Check
        if len(beta) > RECENT_HISTORY_SIZE:
            raise ValueError("Invalid beta length, must be equal to RECENT_HISTORY_SIZE")

        # Step 2
        last: MMR = MMR([])
        if len(beta) > 0:
            last = deepcopy(beta[-1].mmr)

        mmr_functions = MMRFunctions()
        last = mmr_functions.append_fn(last, accumulate_root, Hash.keccak256)

        n = BlockHistory(
            Hash.blake2b(block.header.encode()) if header_hash is None else header_hash,
            last,
            Bytes[32]([0] * 32),
            package(block.extrinsic.guarantees)
        )

        # TODO: Genesis Unclear

        # Step 3
        beta.append(n)

        state.beta = Beta(beta[-8:])

        # Return State
        return state