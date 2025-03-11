from itertools import accumulate

from jam.state.state import State
from jam.types import ReportedWorkPackage
from jam.types.block import Block
from jam.types.base.sequences.bytes import ByteArray32

from jam.authorization.authorization import Authorization
from jam.recent_history.recent_history import RecentHistory
from jam.consensus.safrole.safrole import Safrole
from jam.assurances.assurances import Assurances
from jam.disputes.disputes import Disputes
from jam.preimages.preimages import Preimages
from jam.statistics.statistics import Statistics


def master_transition_state (pre_state : State, block: Block) -> State:
    """
           Master transition state

           args accepted
            pre_state: state before transition

            block: block

           returns new_state
            """

    #section 11 (assurance and the Reporting)
    block_production_state = Safrole.transition(pre_state, block)
    recent_block_history_state = RecentHistory.transition(block_production_state, block, ByteArray32([0]*32))
    authorization_state  = Authorization.transition(recent_block_history_state, block)
    disputes_state = Disputes.transition(authorization_state, block)
    assurance_state = Assurances.transition(disputes_state, block)
    # reporting_state = Report.transition(assurance_state, block) ## TODO: update with latest state oreders.
    # accumulation_state = accumulate.transition(reporting_state, block)
    preimage_state = Preimages.transition(assurance_state, block)
    statistics_state = Statistics.transition(preimage_state, block)

    final_state = statistics_state

    return final_state








