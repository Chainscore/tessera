from jam.types.state.sigma import Sigma
from jam.utils.dummy.dummy_state_comp import create_dummy_state_components


def create_dummy_state() -> Sigma:
    """Create a complete dummy state for testing"""
    return Sigma(**create_dummy_state_components())
