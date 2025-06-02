from jam.execution.pvm.utils import PvmUtilities


def test_b_fn(): 
    a = 100
    a_bits = PvmUtilities.b(a, 1)
    a_derived = PvmUtilities.b_inv(a_bits)
    assert a == a_derived