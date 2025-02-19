import pytest
from jam.types.base.integers import U8, U16, U32, U64, Int


class TestIntegers:
    @pytest.mark.parametrize(
        "int_class,max_value",
        [
            (U8, 255),
            (U16, 65535),
            (U32, 4294967295),
            (U64, 18446744073709551615),
        ],
    )
    def test_initialization(self, int_class, max_value):
        """Test integer initialization and bounds."""
        # Valid cases
        assert int_class(0).value == 0
        assert int_class(max_value).value == max_value

        # Invalid cases
        with pytest.raises(ValueError):
            int_class(-1)
        with pytest.raises(ValueError):
            int_class(max_value + 1)
        with pytest.raises(TypeError):
            int_class("123")
        with pytest.raises(TypeError):
            int_class(12.34)

    @pytest.mark.parametrize("int_class", [U8, U16, U32, U64])
    def test_arithmetic(self, int_class):
        """Test arithmetic operations."""
        a = int_class(10)
        b = int_class(3)

        assert isinstance(a + b, int_class)
        assert a + b == int_class(13)
        assert a - b == int_class(7)
        assert a * b == int_class(30)
        assert a // b == int_class(3)
        assert a % b == int_class(1)

    @pytest.mark.parametrize("int_class", [U8, U16, U32, U64])
    def test_comparisons(self, int_class):
        """Test comparison operations."""
        a = int_class(10)
        b = int_class(3)

        assert b < a
        assert b <= a
        assert a > b
        assert a >= b
        assert a != b
        assert a == int_class(10)

        # Compare with Python int
        assert a > 3
        assert a == 10
        assert a < 20

    @pytest.mark.parametrize("int_class", [U8, U16, U32, U64])
    def test_codec(self, int_class):
        """Test encoding/decoding."""
        original = int_class(42)
        encoded = original.encode()
        decoded, size = int_class.decode_from(encoded)

        assert isinstance(decoded, int_class)
        assert decoded == original
        assert size == int_class.byte_size

    def test_general_int(self):
        """Test GeneralInt specific functionality."""
        # Test larger values
        large_value = 1 << 32  # Too big for U32
        g = Int(large_value)
        encoded = g.encode()
        decoded, _ = Int.decode_from(encoded)
        assert decoded == g

        # Test encoding size varies with value
        small = Int(5)
        large = Int(1 << 32)
        assert len(small.encode()) < len(large.encode())

    @pytest.mark.parametrize("int_class", [U8, U16, U32, U64, Int])
    def test_protocol_methods(self, int_class):
        """Test Python protocol methods."""
        value = int_class(42)

        # __int__
        assert int(value) == 42

        # __index__ (for slicing)
        lst = [1, 2, 3, 4, 5]
        assert lst[value % 5] == 3

        # __hash__
        d = {value: "test"}
        assert d[int_class(42)] == "test"

        # __repr__
        assert repr(value) == f"{int_class.__name__}(42)"
