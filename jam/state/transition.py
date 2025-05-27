from typing import Any

from jam.accumulation.accumulation import Accumulation
from jam.report.state import Reporting
from jam.authorization.authorization import Authorization
from jam.recent_history.recent_history import RecentHistory
from jam.consensus.safrole.safrole import Safrole
from jam.assurances.assurances import Assurances
from jam.disputes.disputes import Disputes
from jam.preimages.preimages import Preimages
from jam.statistics.statistics import Statistics
from jam.types import Block, ByteArray32


def transition(state: Any, block: Block) -> "State":
    """
    Main state transition function. Takes in the current state and the incoming block, returns the transitioned state

    Args:
        pre_state: Current state
        block: Incoming block

    Returns:
        State: The transitioned state
    """

    # TODO: Validate block headers
    # Epoch markers - make sure eta0_1 are the same as current etas
    # Tickets mark - make sure tickets are valid, present in gamma_a and outside in sequenced
    # Offenders mark - make sure offenders are present in psi.offenders

    # 1. Safrole
    entropy = ByteArray32(bytes(32))
    sigma = Safrole.transition(state, block, entropy)
    # 2. Disputes
    sigma = Disputes.transition(sigma, block)
    # 3. Assurances
    sigma = Assurances.transition(sigma, block)
    # 4. Reporting
    sigma = Reporting.transition(sigma, block)
    # 5. Accumulation
    sigma = Accumulation.transition(sigma, block)
    # 6. Authorization
    sigma = Authorization.transition(sigma, block)
    # 7. Recent History
    sigma = RecentHistory.transition(sigma, block, ByteArray32([0] * 32))
    # 8. Preimages
    sigma = Preimages.transition(sigma, block)
    # 9. Statistics
    sigma = Statistics.transition(sigma, block, [], {}, {})

    return sigma
