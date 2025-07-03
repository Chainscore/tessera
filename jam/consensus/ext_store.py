
from typing import List

from structlog import get_logger
from tsrkit_types import TypedVector

from jam.types.block.extrinsics.assurances import AssurancesExtrinsic
from jam.types.block.extrinsics.disputes import Culprits, DisputesExtrinsic, Faults, Verdicts
from jam.types.block.extrinsics.guarantees import GuaranteesExtrinsic, ReportGuarantee
from jam.types.block.extrinsics.preimages import PreimagesExtrinsic
from jam.types.block.extrinsics.tickets import TicketEnvelope
from jam.types.protocol.core import TimeSlot


logger = get_logger("network")

class ExtrinsicStore:
    """Persistent store for extrinsics"""
    eg: GuaranteesExtrinsic
    ep: PreimagesExtrinsic
    et: TypedVector[TicketEnvelope]
    ea: AssurancesExtrinsic
    ed: DisputesExtrinsic

    def __init__(self) -> None:
        self.eg = GuaranteesExtrinsic([])
        self.ep = PreimagesExtrinsic([])
        self.et = TypedVector[PreimagesExtrinsic]([])
        self.ea = AssurancesExtrinsic([])
        self.ed = DisputesExtrinsic(
            verdicts = Verdicts([]),
            culprits = Culprits([]),
            faults = Faults([])
        )
    
    # ----- EG ----- #
    def process_guarantee(self, report_g: ReportGuarantee):
        """Process an incoming report gurantee"""
        # Find if it already exists in eg, if so, update the signatures(add new ones); ignore old ones 
        index = -1
        for i, g in enumerate(self.eg):
            if g.report == report_g.report:
                # if a new val index, add em
                index = i 
        if index == -1:
            # TODO: Validate guarantees + WR 
            self.eg.append(report_g)
        else:
            logger.error("Duplicate Work Report found", report=report_g)

    def remove_guarantee(self, report_g: ReportGuarantee):
        """Remove an imported gurantee"""
        index = -1
        for i, g in enumerate(self.eg):
            if g.report == report_g.report:
                self.eg.pop(i)
        if index == -1:
            logger.warning("Work Report was not collected", report=report_g)

       
    # ----- EA ----- #
    # ----- ET ----- #
    # ----- ED ----- #
    # ----- EP ----- #

ext_store = ExtrinsicStore()
