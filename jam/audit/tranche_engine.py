import asyncio
from time import time

from tsrkit_types.bits import Uint
from tsrkit_types.sequences import TypedVector
from tsrkit_types.dictionary import Dictionary


# from jam.state.state import State
from jam.utils.constants import AUDIT_PERIOD, VALIDATOR_COUNT
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import Hash
from jam.logging import get_logger
from rockstore import RockStore

from jam.audit.tranche import Tranche, TrancheState, AuditRecord
from jam.types.work.report import WorkReportHash

logger = get_logger("tranche_engine")

class TrancheEngine:
    def __init__(self, db: RockStore, slot: TimeSlot):
           self.db = db
           self.slot = slot
           # in-RAM cache: tranche_index → TrancheState
           self._cache: Dictionary[Uint, TrancheState] = Dictionary[Uint, TrancheState]({})
           # make sure tranche #0 is seeded
           self._load_into_cache(Uint(0))

    def _load_into_cache(self, tranche_idx: Uint) -> TrancheState:
        # if we already have it, return it
        if tranche_idx in self._cache:
            return self._cache[tranche_idx]
        # else load from db or empty, then cache it
        self._cache[tranche_idx] = TrancheState.empty()
        return TrancheState.empty()

    async def run(self):
        """
        Run tranche processing for a given slot_index continuously, 8s per tranche.
        """
        tranche_index = Uint(0)

        while True:
            t0 = time()  # tranche start time
            tranche = Tranche(tranche_index=tranche_index - 1, slot_index=self.slot)
            prev_ts= self._cache[tranche_index]
            logger.info(f"⚙️ Running tranche {tranche_index} for slot {self.slot}, auditing {len(prev_ts.unaudited_list)} WRs, valid {len(prev_ts.valid_set)}, invalid {len(prev_ts.invalid_set)}")

            if tranche_index>0:
                # Calling Network Protocol-> Passing state to the nodes for their nodes and judgement/announcement to collect on.
                new_unaudited:TypedVector[WorkReportHash] = TypedVector[WorkReportHash]([])

                for wr in prev_ts.unaudited_list:
                    record: AuditRecord = prev_ts.judgments.get(wr, AuditRecord.empty())

                    true_count = len(record.true_votes)
                    false_count = len(record.false_votes)

                    logger.debug(f"WR {wr.hex()[:8]} | True: {true_count} | False: {false_count}")

                    if (false_count == 0 and len(record.announces)==len(record.true_votes) ) or true_count >= VALIDATOR_COUNT * 2 // 3 :
                        prev_ts.valid_set.append(wr)
                    elif false_count >= VALIDATOR_COUNT * 1 // 3:
                        prev_ts.invalid_set.append(wr)
                    else:
                        new_unaudited.append(wr)


                prev_ts.unaudited_list =TypedVector[WorkReportHash](new_unaudited)
                # updated_tranche=Tranche(tranche_index=tranche_index, slot_index=self.slot)
                # updated_tranche.save_state(self.db, prev_ts)
                if not new_unaudited:
                    if len(prev_ts.invalid_set) > 0:
                        logger.info("❌ Block is INVALID due to invalid WRs")
                    else:
                        logger.info("✅ Block is VALID")
                    logger.info(f"✅ Block audited successfully for slot {self.slot} after tranche {tranche_index}")
                    break;


                logger.info(f"🔄 Moving to tranche {tranche_index + 1} for remaining {len(new_unaudited)} WRs")
                tranche_index += Uint(1)
                logger.info(f"tranche bhai: {tranche_index}")
            else:
                logger.info(f"tranche is 0 bhai: {tranche_index}")
            elapsed = time() - t0
            to_sleep = max(0, AUDIT_PERIOD - elapsed)
            logger.info(f"🔄 Next tranche in {to_sleep:.2f}s")
            await asyncio.sleep(to_sleep)
