import pytest
from jam.types.base.boolean import Boolean


class TestBoolean:
    def test_initialization(self):
        """Test Boolean initialization."""
        # Valid cases
        assert Boolean(True).value is True
        assert Boolean(False).value is False

        # Invalid cases
        with pytest.raises(TypeError):
            Boolean(1)  # type: ignore
        with pytest.raises(TypeError):
            Boolean("true")  # type: ignore
        with pytest.raises(TypeError):
            Boolean(None)  # type: ignore

    def test_bool_protocol(self):
        """Test bool protocol methods."""
        assert bool(Boolean(True)) is True
        assert bool(Boolean(False)) is False

        # Test in boolean context
        if Boolean(True):
            assert True
        else:
            assert False

        if Boolean(False):
            assert False
        else:
            assert True

    def test_equality(self):
        """Test equality comparisons."""
        assert Boolean(True) == Boolean(True)
        assert Boolean(False) == Boolean(False)
        assert Boolean(True) != Boolean(False)

        # Compare with Python bool
        assert Boolean(True) == True  # noqa: E712
        assert Boolean(False) == False  # noqa: E712

        # Compare with other types
        assert Boolean(True) != 1
        assert Boolean(True) != "true"

    def test_hash(self):
        """Test hash implementation."""
        assert hash(Boolean(True)) == hash(True)
        assert hash(Boolean(False)) == hash(False)

        # Test in sets/dicts
        s = {Boolean(True), Boolean(False)}
        assert len(s) == 2
        assert Boolean(True) in s
        assert Boolean(False) in s

    def test_codec(self):
        """Test encoding/decoding."""
        for value in [True, False]:
            b = Boolean(value)
            encoded = b.encode()
            decoded, size = Boolean.decode_from(encoded)

            assert isinstance(decoded, Boolean)
            assert decoded.value == value
            assert size == 1  # Boolean always uses 1 byte

    def test_repr(self):
        """Test string representation."""
        assert repr(Boolean(True)) == "Boolean(True)"
        assert repr(Boolean(False)) == "Boolean(False)"
