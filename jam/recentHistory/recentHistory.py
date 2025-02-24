import hashlib
import dataclasses
from jam.merklization import MMR,MMRFunctions
from jam.merklization.mountain_merkle import OptionHash
from jam.state.state import State
from jam.types import ByteArray32, Vector, HeaderHash
from jam.types.block import Block
from jam.types.extrinsics import GuaranteesExtrinsic
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.protocol.crypto import Hash, OpaqueHash
# from jam.utils.codec.decorators import dataclasses
from jam.utils.constants import RECENT_HISTORY_SIZE
from jam.state.components.beta import BlockHistory, PackageDict


def package(block:GuaranteesExtrinsic) -> PackageDict:
    package_Dict:PackageDict[WorkPackageHash, SegmentRoot]=PackageDict()
    for x in block:
        a= x.report.segment_root_lookup
        for c in a:
            b= c.work_package_hash
            d =c.segment_tree_root
            package_Dict[b]=d

    # print('l13')
    return package_Dict


class RecentHistory:

    @staticmethod
    def transition(pre_state: State, block:Block, header_hash: HeaderHash, accumulate_root: OpaqueHash) -> State:

        # print("In transition", pre_state.beta)
        mmr_func = MMRFunctions()
        new_state: State = dataclasses.replace(pre_state)
        if(len(new_state.beta)):
            new_state.beta[-1].state_root = block.header.parent_state_root

        if len(new_state.beta) > RECENT_HISTORY_SIZE:
            raise ValueError("Invalid beta length, must be equal to CORE_COUNT")

        last:Vector(OptionHash) = []
        if len(new_state.beta) > 0:
            last=new_state.beta[-1].mmr
        
        # n = BlockHistory(Hash.blake2b(block.header.encode()), mmr_func.append_fn(last,block.accumulation_root,Hash.blake2b), ByteArray32([0] * 32), package(block.extrinsic.guarantees))
        n = BlockHistory(header_hash, mmr_func.append_fn(last,accumulate_root,Hash.blake2b), ByteArray32([0] * 32), package(block.extrinsic.guarantees))

        # print('l10')
        # n.header_hash = Hash.blake2b(block.header.encode())
        # print('l11')
        # n.state_root = ByteArray32([0] * 32)
        # n.mmr = mmr_func.append_fn(last,block.accumulation_root,Hash.blake2b)
        # print('l6',type(block.extrinsic.guarantees))
        # n.packages = package(block.extrinsic.guarantees)
        # print('l7', type(n), type(new_state.beta))

        new_state.beta.append(n)
        # print('l8')
        # new_state.beta = new_state.beta[-8:]
        # print('l9')

        return new_state
        



