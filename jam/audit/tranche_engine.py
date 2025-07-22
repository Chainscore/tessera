import asyncio
# from time import time

from tsrkit_types.bits import Uint
from tsrkit_types.sequences import TypedVector

from jam.audit.audit_process import AuditProcess
from jam.types.block.extrinsics.disputes import Culprits, Faults, Verdicts
from jam.utils.constants import AUDIT_PERIOD, VALIDATOR_COUNT
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.core import TrancheIndex
from jam.types.protocol.crypto import Hash, HeaderHash
from jam.logging import get_logger

from jam.operations.tranche_store import Tranche, TrancheState, JudgmentRecord, TrancheStore,tranche_store
from jam.types.work.report import WorkReport, WorkReportHash

logger = get_logger("tranche_engine")

class TrancheEngine:
    def __init__(self):
        self.store = tranche_store

    async def run(self, header_hash:HeaderHash):
        """
        Run tranche processing for a given header_hash continuously, 8s per tranche.
        """
        tranche_index = TrancheIndex(0)
        present_state=self.store._get_state(tranche=Tranche(tranche_index=tranche_index,header_hash=header_hash))
        while True:
            from jam.operations.ext_store import ext_store
            initTranche=Tranche(header_hash=header_hash,tranche_index=tranche_index)

            ts: TrancheState = self.store._get_state(initTranche)
            logger.info(f"⚙️ Running tranche {tranche_index} for header {header_hash}, auditing {len(ts.unaudited_list)} WRs, valid {len(ts.valid_set)}, invalid {len(ts.invalid_set)}")
            #TODO: Sending the store through the task for the auditors to save their judgement & announcements in the store itself
            # asyncio.create_task(AuditProcess.audit_process(newly_avail_wrs=ts.unaudited_list,store=self.store,tranche=initTranche))

            if tranche_index>0:
                new_unaudited:TypedVector[WorkReport] = TypedVector[WorkReport]([])

                for wr in ts.unaudited_list:
                    record: JudgmentRecord = ts.judgments.get(wr.encode(), JudgmentRecord.empty())

                    true_count = len(record.true_votes)
                    false_count = len(record.false_votes)
                    logger.debug(f"WR {wr.encode().hex()[:8]} | True: {true_count} | False: {false_count} | Accnouncements: {len(record.announces)} | Tranche: {tranche_index}")
                    # TODO: Will change this true count condition which is !mentioned in GP
                    if true_count!=0 and (false_count == 0 and true_count >= VALIDATOR_COUNT * 2 // 3 or len(record.announces)==len(record.true_votes)):
                        ts.valid_set.append(wr)
                    elif false_count >= VALIDATOR_COUNT * 1 // 3:
                        verdicts:Verdicts=Verdicts([])
                        culprits: Culprits = Culprits([])
                        faults:Faults=Faults([])
                        ext_store.import_disp(verdicts,culprits,faults)
                        ts.invalid_set.append(wr)
                    else:
                        new_unaudited.append(wr)


                ts.unaudited_list =TypedVector[WorkReport](new_unaudited)

                # print("new audits",ts.unaudited_list,ts.invalid_set,ts.valid_set)
                if not new_unaudited:
                    if len(ts.invalid_set) > 0:
                        logger.info("❌ Block is INVALID due to invalid WRs")
                    else:
                        logger.info("✅ Block is VALID")
                    logger.info(f"✅ Block audited successfully for header {header_hash} after tranche {tranche_index}")
                    break;

                logger.info(f"🔄 Moving to tranche {tranche_index} for remaining {len(new_unaudited)} WRs")

            tranche_index += TrancheIndex(1)

            updated_tranche=Tranche(header_hash=header_hash,tranche_index=tranche_index)


            self.store._save_state(updated_tranche, ts)
            logger.info(f"tranche bhai: {tranche_index}")

            await asyncio.sleep(AUDIT_PERIOD)
