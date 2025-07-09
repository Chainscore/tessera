
from typing import List

from structlog import get_logger
from jam.types.protocol.crypto import Hash
from tsrkit_types import TypedVector

from jam.preimages import preimages
from jam.types.block.block import Block
from jam.types.block.extrinsics.assurances import AssurancesExtrinsic, AvailAssurance
from jam.types.block.extrinsics.disputes import Culprits, DisputesExtrinsic, Faults, Verdicts
from jam.types.block.extrinsics.guarantees import GuaranteesExtrinsic, ReportGuarantee
from jam.types.block.extrinsics.preimages import Preimage, PreimagesExtrinsic
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
    def import_rg(self, report_g: ReportGuarantee):
        """
        Process an incoming report gurantee
        """
        # Find if it already exists in eg, if so, update the signatures(add new ones); ignore old ones 
        logger.info("Storing Report Guarantee", report=report_g.to_json(), hash=Hash.blake2b(report_g.encode()).hex()[:16]+"...")
        index = -1
        for i, g in enumerate(self.eg):
            if g.report == report_g.report:
                # if a new val index, add em
                index = i 
        if index == -1:
            # TODO: Validate guarantees + WR 
            self.eg.append(report_g)
        else:
            logger.error("Duplicate Work Report found", report=report_g.to_json())

    def rm_rg(self, report_g: ReportGuarantee):
        """
        Remove an imported report gurantee
        Logs a warning if we had not collected the extrinsic. This implies our netwokring didn't fn properly.
        """
        index = -1
        for i, g in enumerate(self.eg):
            if g.report == report_g.report:
                self.eg.pop(i)
        if index == -1:
            logger.warning("Work Report was not collected", report=report_g)

       
    # ----- EA ----- #
    def import_assr(self, assr: AvailAssurance):
        """
        Process an incoming assurance 
        """
        print("Received assurance")
        if assr in self.ea:
            logger.error("Duplicate Assurance found", assurance=assr.to_json())
            return 
        self.ea.append(assr)
    
    def rm_assr(self, assr: AvailAssurance):
        try:
            indx = self.ea.index(assr)
            self.ea.pop(indx)
        except ValueError as e:
            logger.warning("Assurance was not collected", error=e, assurance=assr.to_json())
            return 
    
    # ----- ET ----- #
    def import_tkt(self, tkt: TicketEnvelope):
        """
        Process an incoming ticket  
        """
        if tkt in self.et:
            logger.error("Duplicate Ticket found", ticket=tkt.to_json())
            return 
        self.et.append(tkt)
    
    def rm_tkt(self, tkt: TicketEnvelope):
        try:
            indx = self.et.index(tkt)
            self.et.pop(indx)
        except ValueError as e:
            logger.warning("Ticket was not collected", error=e, ticket=tkt.to_json())
            return 
    
    # TODO: ----- ED ----- #


    # ----- EP ----- #
    def import_pimg(self, pimg: Preimage):
        """
        Process an incoming preimage 
        """
        if pimg in self.ep:
            logger.error("Duplicate Preimage found", ticket=tkt.to_json())
            return 
        self.ep.append(pimg)
    
    def rm_pimg(self, pimg: Preimage):
        try:
            indx = self.ep.index(pimg)
            self.ep.pop(indx)
        except ValueError as e:
            logger.warning("Preimage was not collected", error=e, ticket=tkt.to_json())
            return 
    

    def clear_on_import(self, block: Block):
        # Remove Preimages 
        for preimage in block.extrinsic.preimages:
            self.rm_pimg(preimage)
        # Remove Tickets
        for ticket in block.extrinsic.tickets:
            self.rm_tkt(ticket)
        # Remove Assurances 
        for assurance in block.extrinsic.assurances:
            self.rm_assr(assurance)
        # Remove WRs
        for grte in block.extrinsic.guarantees:
            self.rm_rg(grte)
        # TODO: Remove disputes 

        return

ext_store = ExtrinsicStore()
