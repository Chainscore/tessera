from rockstore import RockStore

from jam.state.ghost import GhostState
from jam.state.state import setup_state
from jam.work_package.guarantor_assignments import guarantor_assignments


def test_guarantor_assign(db_path):
    db = RockStore(db_path)
    state = setup_state(db, GhostState.genesis())

    mapping = guarantor_assignments(state)
