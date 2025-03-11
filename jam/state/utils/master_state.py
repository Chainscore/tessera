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

    state = pre_state
    #section 11 (assurance and the Reporting)
    # state = Safrole.transition(pre_state, block)
    state = RecentHistory.transition(state, block, ByteArray32([0]*32)) # NOTE::Working
    state  = Authorization.transition(state, block) 
    state = Disputes.transition(state, block) # NOTE::Working
    state = Assurances.transition(state, block)
    # reporting_state = Report.transition(assurance_state, block) ## TODO: update with latest state oreders.
    # accumulation_state = accumulate.transition(reporting_state, block) ## TODO:
    state = Preimages.transition(state, block)
    state = Statistics.transition(state, block) # NOTE::Working

    final_state = state

    return final_state








