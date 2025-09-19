import asyncio
from tsrkit_types import U32, Uint, U8, Null
from jam.types.work.report import WorkReport
from jam.block.block import Block
from jam.types.work.report import WorkReportHash
from jam.types.audit.audit_tranche import Tranche
from jam.logging import get_logger

# Module-specifier logger
logger = get_logger("utils")


class Utils:

    @classmethod
    async def fetch_report(cls, wr_hash: WorkReportHash) -> WorkReport | None:
        """
        Fetch Work Report.
        1. Check in ReportDA (local)
        2. Request from other Auditor via protocol 136 if not found.
        Returns:
            WorkReport if found
        Raises:
            KeyError if not found anywhere
            NetworkingError if protocol 136 failed
        """

        # 1. check in ReportDA
        #
        from jam.settings import settings
        from jam.storage.da.reports import ReportsDA
        from jam.network.protocols.ce_136 import WorkReportRequest, CE136Data, CE136Response

        CE136 = WorkReportRequest()

        reports_da = ReportsDA(settings.d3l)
        work_report : WorkReport | None = reports_da.get(wr_hash=wr_hash)

        if work_report is not None:
            return work_report

        try:
            logger.info(
                "Work Report not found in ReportsDA, requesting via protocol 136",
                wr_hash=wr_hash,
            )
            report_hash = WorkReportHash(wr_hash)

            data = CE136Data(len=U32(len(report_hash.encode())), work_report_hash=report_hash)

            wr = await CE136.transmit(data=data)

            if wr.hash() != wr_hash:
                logger.error("Received mismatched WorkReport from protocol 136")
                return None

            return wr

        except asyncio.TimeoutError:
            logger.warning("Timeout while requesting Work Report via protocol 136", wr_hash=wr_hash)

        except Exception as e:
            logger.exception("Failed to fetch Work Report via protocol 136", wr_hash=wr_hash, exc=e)
            raise KeyError(f"Work Report not found for hash {wr_hash}")

    @classmethod
    async def process_refine(cls, wr_hash : WorkReportHash, tranche: Tranche) -> U8 | None:
        """
        Check whether the given Work Report has already been refined.

        Refinement can be skipped if either:
          1. The report was refined in any previous tranche.
          2. The report was already refined during the guarantee process.
          3. If neither condition (1) nor (2) is true, then perform refinement now.

        Args:
            wr_hash:
            tranche: Work Report tranche
        """

        from jam.settings import settings
        from jam.storage.tranche_audit_store import tranche_store
        from jam.types.audit.audit_tranche import TrancheState
        from jam.audit.audit import Audit
        from rockstore import RockStore

        audit =  Audit()

        tranche_index = tranche.tranche_index
        header_hash = tranche.header_hash
        validator_index = -settings.validator_index

        state = tranche_store.get_state(tranche=tranche)

        # Get state records
        audit_record = state.records[wr_hash]
        announces = audit_record.announces
        true_votes = audit_record.true_votes
        false_votes = audit_record.false_votes

        if validator_index in true_votes:
            logger.info(
                f"already true judgment given in prev tranche for Work report: {wr_hash}"
            )
            return None

        elif validator_index in false_votes:
            logger.info(
                f"already false judgment given in prev tranche for Work report: {wr_hash}"
            )
            return None

        else:
            # 2. -------------- Guarantee refine check -------------------
            block = Block.load(header_hash=header_hash, db=settings.main_db)
            guarantee_found = False

            guarantee_ext = block.extrinsic.guarantees
            for guarantee in guarantee_ext:
                if guarantee.report.hash() == wr_hash:
                    guarantee_found = True
                    break

            if guarantee_found:
                return U8(1)

            else:
                wr = await cls.fetch_report(wr_hash=wr_hash)
                if wr is not None:
                    validity = await audit.refine(wr=wr)
                    return validity