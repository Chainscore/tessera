# tests/unit/test_types.py

import pytest
from jam.core.types import Balance, ServiceId

def test_balance_operations():
    b1 = Balance(100)
    b2 = Balance(50)
    
    assert (b1 + b2).value == 150
    assert (b1 - b2).value == 50
    
    with pytest.raises(ValueError):
        Balance(-1)

def test_service_id():
    sid = ServiceId(1)
    assert sid.index == 1
    
    with pytest.raises(ValueError):
        ServiceId(-1)