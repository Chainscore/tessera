from tsrkit_types import Vector

from jam.storage.tranche_store import tranche_store
from jam.types.audit.tranche import TrancheIndex, Tranche, TrancheState
from jam.state.transitions.disputes.disputes import Disputes               #class of dispute state transition
from jam.utils.constants import AUDIT_PERIOD, CURRENT_TIME, SLOT_PERIOD
from jam.types.protocol.core import ValidatorIndex
from jam.block.extrinsics.disputes import DisputesExtrinsic

class DisputeExtrinsic:


    @staticmethod
    def build_dispute(negative_judgment : Vector[ValidatorIndex]) -> DisputesExtrinsic:
        ...

dispute_extrinsic = DisputeExtrinsic()
