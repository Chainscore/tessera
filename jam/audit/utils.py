from tsrkit_types import U32
from jam.types.work.report import WorkReport
from jam.block.block import Block
from jam.types.work.report import WorkReportHash
from jam.types.audit.audit_tranche import Tranche

from jam.logging import get_logger

# Module-specifier logger
logger = get_logger("auditor")


class Utils:

    @classmethod
    async def getting_report(cls, wr_hash: WorkReportHash) -> WorkReport | bool:
        """
        fetch Work Report if it is not exist in Report
        1. check in ReportDA
        2. using protocol 136
        """
        # 1. check in ReportDA
        #
        from jam.settings import settings
        from jam.storage.da.reports import ReportsDA
        from jam.network.protocols.ce_136 import WorkReportRequest, CE136Data, CE136Response

        CE136 = WorkReportRequest()

        d3l = settings.d3l
        reports_da = ReportsDA(d3l)
        report = reports_da.get(wr_hash=wr_hash)

        # 2. using protocol 136
        if type(report) == WorkReportHash:
            return report
        else:
            logger.info(
                "Work Report Not found in RepostDA, Now request to the other Auditor via protocol 136"
            )
            report_hash = WorkReportHash(wr_hash)

            data = CE136Data(len=U32(len(report_hash.encode())), work_report_hash=report_hash)

            response = await CE136.transmit(data=data)

            if type(response) == WorkReportHash:
                return response
            else:
                logger.debud("No work report was found in ReportDA and under protocol 136.")
                return False

    @classmethod
    async def process_refine(cls, block: Block, wr: WorkReport, tranche: Tranche) -> bool:
        """Check previously refine or not"""

        from jam.settings import settings
        from jam.storage.tranche_audit_store import tranche_store

        curr_tranche = tranche
        tranche_index = curr_tranche.tranche_index
        validator_index = settings.validator_index

        wr_hash = wr.hash()

        # ---------------------------- Check => already refine or not ----------------------------------------
        # 1. Guarantee refine check
        # does neet to check past blocks ????????????
        guarantee_refine = False
        guarantee_ext = block.extrinsic.guarantees
        for report, slot, signature in guarantee_ext:
            if report.hash() == wr_hash:
                logger.info(f"already judgment given for Work report: {wr_hash}")
                guarantee_refine = True
                break

        if guarantee_refine:
            return True

        elif guarantee_refine == False and tranche_index > 0:
            # 2. previous tranche refine check
            curr_state = tranche_store.get_state(
                tranche=curr_tranche
            )  # WHY CURRENT STATE BECAUSE WE CARRY FORWARD PREVIOUS JUDGMENT TO NEXT TRANCHE STATE
            records = curr_state.records[wr_hash]
            true_votes = records.no_shows
            false_votes = records.false_votes
            if validator_index in true_votes:
                logger.info(
                    f"already true judgment given in prev tranche for Work report: {wr_hash}"
                )
                return True

            elif validator_index in false_votes:
                logger.info(
                    f"already false judgment given in prev tranche for Work report: {wr_hash}"
                )
                return False
            else:
                validity = await cls.refine(wr=wr)
                return validity

        else:
            logger.info(
                f" Work Report hsa not been refine via validator: {validator_index} => {wr_hash},"
            )
            logger.info(f"Process refine for Work Report : {wr_hash}")
            validity = await cls.refine(wr=wr)
            return validity
