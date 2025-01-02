"""Unit tests for bit sequence types."""

import pytest
from jam.types.base.integers import U8
from jam.types.base.option import Option

class TestOption:
    """Test suite for option types."""

    def test_option(self):
        """Test creation of Option."""
        a = Option(U8(1))
        assert a.value == U8(1)