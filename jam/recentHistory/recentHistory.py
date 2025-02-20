import hashlib

from jam.merklization import MountainMerkle
from jam.merklization.mountain_merkle import OptionHash
from jam.state.state import State
from jam.types import ByteArray32, Vector, Dictionary
from jam.types.block import Block
from jam.types.extrinsics import GuaranteesExtrinsic
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.protocol.crypto import Hash
from jam.utils.codec.decorators import dataclasses
from jam.utils.constants import RECENT_HISTORY_SIZE
from jam.state.components.beta import BlockHistory


def package(block:GuaranteesExtrinsic):
    package_Dict:Dictionary[WorkPackageHash, SegmentRoot]
    for x in block:
        a= x.report.segment_root_lookup
        for c in a:
            b= c.work_package_hash
            d =c.segment_tree_root
            package_Dict[b]=d

    return package_Dict


class RecentHistory:

    @staticmethod
    def transition(pre_state: State, block:Block) -> State:

        mmr = MountainMerkle()
        new_State = dataclasses.replace(pre_state)
        new_State.beta[-1].state_root = block.header.parent_state_root

        if len(new_State.beta) > RECENT_HISTORY_SIZE:
            raise ValueError("Invalid beta length, must be equal to CORE_COUNT")

        last:Vector(OptionHash) = []
        if len(new_State.beta)>0:
            last=new_State.beta[-1].mmr_root
        
        n = BlockHistory

        n.header_hash = Hash.blake2b(block.header.encode())
        n.state_root = ByteArray32([0] * 32)
        n.mmr = mmr.append_fn(last,Block.accumulation_root,Hash.blake2b)
        n.packages = package(block.extrinsic.guarantees)

        new_State.beta.append(n)
        new_State.beta = new_State.beta[-8:]

        return new_State
        



