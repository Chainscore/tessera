from jam.accumulation.accumulation import Accumulation
from jam.report.state import Reporting
from jam.state.state import State
from jam.types.block import Block
from jam.types.base.sequences.bytes import ByteArray32

from jam.authorization.authorization import Authorization
from jam.recent_history.recent_history import RecentHistory
from jam.consensus.safrole.safrole import Safrole
from jam.assurances.assurances import Assurances
from jam.disputes.disputes import Disputes
from jam.preimages.preimages import Preimages
from jam.statistics.statistics import Statistics


def transition(pre_state: State, block: Block) -> State:
    """
    Main state transition function. Takes in the current state and the incoming block, returns the transitioned state

    Args:
        pre_state: Current state
        block: Incoming block

    Returns:
        State: The transitioned state
    """

    # 1. Safrole
    entropy = ByteArray32(bytes(32)) 
    safrole_state = Safrole.transition(pre_state, block, entropy)
    # 2. Disputes
    disputes_state = Disputes.transition(safrole_state, block)
    # 3. Assurances
    assurance_state, available_wrs = Assurances.transition(disputes_state, block)
    # 4. Reporting
    reporting_state = Reporting.transition(assurance_state, block)
    # 5. Accumulation
    accumulation_state = Accumulation.transition(reporting_state, block)
    # 6. Authorization
    authorization_state = Authorization.transition(accumulation_state, block)
    # 7. Recent History
    recent_block_history_state = RecentHistory.transition(authorization_state, block, ByteArray32([0] * 32))
    # 8. Preimages
    preimage_state = Preimages.transition(recent_block_history_state, block)
    # 9. Statistics
    #NOTE: temp stats that should come from accumulation module
    accumulation_stats = {}
    deferred_transfer_stats = {}
    statistics_state = Statistics.transition(preimage_state, block, available_wrs, accumulation_stats, deferred_transfer_stats)

    return statistics_state






