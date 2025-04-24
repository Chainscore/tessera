from jam.state.state import State

def test_random_state():
    state_a = State.from_random()
    state_b = State.from_random()
    assert state_a != state_b