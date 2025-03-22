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
    safrole_state = Safrole.transition(pre_state, block)
    # 2. Recent History
    recent_block_history_state = RecentHistory.transition(safrole_state, block, ByteArray32([0] * 32))
    # 3. Authorization
    authorization_state = Authorization.transition(recent_block_history_state, block)
    # 4. Disputes
    disputes_state = Disputes.transition(authorization_state, block)
    # 5. Assurances
    assurance_state = Assurances.transition(disputes_state, block)
    # 6. Reporting
    reporting_state = Reporting.transition(assurance_state, block)
    # 7. Accumulation
    accumulation_state = Accumulation.transition(reporting_state, block)
    # 8. Preimages
    preimage_state = Preimages.transition(accumulation_state, block)
    # 9. Statistics
    statistics_state = Statistics.transition(preimage_state, block)

    return statistics_state






