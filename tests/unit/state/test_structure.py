"""
Sigma (state) structure tests — encode/decode roundtrip.

Pure unit tests — no fixtures, no chain.
"""
from jam.types.state.sigma import Sigma
from jam.utils.dummy.dummy_state import create_dummy_state


def test_encode_decode_roundtrip():
    state = create_dummy_state()
    encoded = state.encode()
    decoded, _ = Sigma.decode_from(encoded)
    assert state == decoded


def test_sigma_has_fields():
    s = create_dummy_state()
    for field in ['tau', 'kappa', 'gamma', 'eta', 'rho', 'pi', 'beta', 'delta']:
        assert hasattr(s, field)


def test_encoded_is_nonzero():
    enc = create_dummy_state().encode()
    assert len(enc) > 0
    assert enc != bytes(len(enc))
