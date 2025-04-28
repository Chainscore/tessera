from jam.state.state import State
from tests.dummy.dummy_state_comp import create_dummy_state_components


def create_dummy_state() -> State:
    """Create a complete dummy state for testing"""
    return State(**create_dummy_state_components())
