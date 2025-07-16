import asyncio
from time import time

from tsrkit_types.bits import Uint
from tsrkit_types.sequences import TypedVector

from jam.state.state import State
from jam.utils.constants import AUDIT_PERIOD, VALIDATOR_COUNT
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import Hash
from jam.logging import get_logger
from rockstore import RockStore

from jam.audit.tranche import Tranche, TrancheState, JudgmentRecord, TrancheStore
from jam.types.work.report import WorkReportHash

logger = get_logger("tranche_engine")

class TrancheEngine:
    def __init__(self, store: TrancheStore):
        self.store = store

    async def run(self, slot_index: Uint):
        """
        Run tranche processing for a given slot_index continuously, 8s per tranche.
        """
        tranche_index = Uint(1)

        while True:
            tranche = Tranche(tranche_index=tranche_index - 1, slot_index=slot_index)
            ts: TrancheState = self.store.load(tranche)
            logger.info(f"⚙️ Running tranche {tranche_index} for slot {slot_index}, auditing {len(ts.unaudited_list)} WRs, valid {len(ts.valid_set)}, invalid {len(ts.invalid_set)}")

            new_unaudited:TypedVector[WorkReportHash] = TypedVector[WorkReportHash]([])

            for wr in ts.unaudited_list:
                record: JudgmentRecord = ts.judgments.get(wr, JudgmentRecord.empty())

                true_count = len(record.true_votes)
                false_count = len(record.false_votes)

                logger.debug(f"WR {wr.hex()[:8]} | True: {true_count} | False: {false_count}")

                if false_count == 0 and true_count >= VALIDATOR_COUNT * 2 // 3 or len(record.announces)==len(record.true_votes):
                    ts.valid_set.append(wr)
                elif false_count >= VALIDATOR_COUNT * 1 // 3:
                    ts.invalid_set.append(wr)
                else:
                    new_unaudited.append(wr)


            ts.unaudited_list =TypedVector[WorkReportHash](new_unaudited)
            updated_tranche=Tranche(tranche_index=tranche_index, slot_index=slot_index)
            self.store.save(updated_tranche, ts)
            # print("new audits",ts.unaudited_list,ts.invalid_set,ts.valid_set)
            if not new_unaudited:
                if len(ts.invalid_set) > 0:
                    logger.info("❌ Block is INVALID due to invalid WRs")
                else:
                    logger.info("✅ Block is VALID")
                logger.info(f"✅ Block audited successfully for slot {slot_index} after tranche {tranche_index}")
                break;


            logger.info(f"🔄 Moving to tranche {tranche_index + 1} for remaining {len(new_unaudited)} WRs")
            tranche_index += Uint(1)
            logger.info(f"tranche bhai: {tranche_index}")

            await asyncio.sleep(AUDIT_PERIOD)
            # await asyncio.sleep(2)
