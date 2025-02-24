from jam.state.state import State
from jam.state.components.beta import BlockHistory, PackageDict
from jam.types import ByteArray32
from jam.types.block import Block
from jam.types.extrinsics import GuaranteesExtrinsic
from jam.types.protocol.crypto import Hash
from jam.merklization import OptionHash, MMRFunctions, MMR
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import RECENT_HISTORY_SIZE
from jam.types.protocol.core import WorkPackageHash, SegmentRoot

from jam.types.base.sequences.vector import Vector

import dataclasses

def package(packages: GuaranteesExtrinsic) -> PackageDict:
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

        new_state: State = dataclasses.replace(pre_state)

        if len(new_state.beta):
            new_state.beta[-1].state_root = block.header.parent_state_root

        if len(new_state.beta) > RECENT_HISTORY_SIZE:
            raise ValueError("Invalid beta length, must be equal to RECENT_HISTORY_SIZE")

        last: MMR = MMR([])
        if len(new_state.beta) > 0:
            last = new_state.beta[-1].mmr

        # n = BlockHistory(Hash.blake2b(block.header.encode()), mmr_func.append_fn(last,block.accumulation_root,Hash.blake2b), ByteArray32([0] * 32), package(block.extrinsic.guarantees))
        mmrFunctions = MMRFunctions()

        n = BlockHistory(
            block.header.parent,
            mmrFunctions.append_fn(last, accumulate_root, Hash.keccak256),
            ByteArray32([0] * 32),
            package(block.extrinsic.guarantees)
        )

        new_state.beta.append(n)
        new_state.beta = new_state.beta[-8:]
        return new_state