from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol, TypeVar, Generic, Final, ClassVar

C = TypeVar('C', bound='CurveProtocol')

class CurveProtocol(Protocol):
    """Protocol defining required curve operations for points."""
    PRIME_FIELD: int
    ORDER: int
    Z: int

class PointProtocol(Protocol[C]):
    """Protocol defining the interface for curve points."""
    x: int
    y: int
    curve: C
    
    def __add__(self, other: 'PointProtocol[C]') -> 'PointProtocol[C]': ...
    def __mul__(self, scalar: int) -> 'PointProtocol[C]': ...
    def is_on_curve(self) -> bool: ...

@dataclass(frozen=True)
class Point(Generic[C]):
    """
    Base implementation of an elliptic curve point.
    
    This class provides the foundation for specific curve point implementations,
    including basic point operations and encoding/decoding functionality.
    
    Attributes:
        x: x-coordinate
        y: y-coordinate
        curve: The curve this point belongs to
    """
    x: Final[int]
    y: Final[int]
    curve: Final[C]
    
    # Class constants
    ENCODING_LENGTH: ClassVar[int] = 32
    
    def __post_init__(self) -> None:
        """Validate point after initialization."""
        if not self._validate_coordinates():
            raise ValueError("Invalid point coordinates")
        if not self.is_on_curve():
            raise ValueError("Point is not on the curve")
    
    def _validate_coordinates(self) -> bool:
        """
        Validate point coordinates are within field bounds.
        
        Returns:
            bool: True if coordinates are valid
        """
        return (
            0 <= self.x < self.curve.PRIME_FIELD and
            0 <= self.y < self.curve.PRIME_FIELD
        )
    
    @abstractmethod
    def is_on_curve(self) -> bool:
        """
        Check if the point lies on the curve.
        
        Returns:
            bool: True if point is on curve
            
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Must be implemented by subclass")
    
    def point_to_string(self) -> bytes:
        """
        Convert elliptic curve point (x, y) to compressed octet string.
        - The y-coordinate is encoded as 32 bytes.
        - The most significant bit of the last byte indicates the sign of the x-coordinate.

        Args:
            self: The point (x, y) to convert

        Returns:
            bytes: The compressed point representation
        """
        p = self.curve.PRIME_FIELD
        p_half = (p - 1) // 2
        x, y = self.x, self.y
        y_bytes = bytearray(y.to_bytes(32, "little"))  # Encode y in little-endian
        x_sign_bit = 1 if x >= p_half else 0  # Sign is set if x >= p/2
        y_bytes[-1] |= (x_sign_bit << 7)
        return bytes(y_bytes)

    @classmethod
    def string_to_point(cls, encoded: bytes, curve: C) -> 'Point[C]':
        """
        Convert compressed octet string back to point.
        
        Args:
            encoded: Compressed point bytes
            curve: The curve to create point on
            
        Returns:
            Point: Decoded point
            
        Raises:
            ValueError: If encoding is invalid
        """
        if len(encoded) != cls.ENCODING_LENGTH + 1:
            raise ValueError("Invalid encoding length")
            
        header = encoded[0]
        if header not in (2, 3):
            raise ValueError("Invalid header byte")
            
        x = int.from_bytes(encoded[1:], 'big')
        if x >= curve.PRIME_FIELD:
            raise ValueError("x-coordinate out of range")
            
        # Recover y-coordinate (implementation depends on curve)
        y = cls._recover_y(x, header & 1, curve)
        
        return cls(x, y, curve)
    
    @staticmethod
    def _recover_y(x: int, y_parity: int, curve: C) -> int:
        """
        Recover y-coordinate from x and parity.
        
        Args:
            x: x-coordinate
            y_parity: Parity of y (0 or 1)
            curve: Curve parameters
            
        Returns:
            int: Recovered y-coordinate
            
        Raises:
            ValueError: If y cannot be recovered
        """
        raise NotImplementedError("Must be implemented by subclass")
    
    @staticmethod
    def _get_bit(data: bytes, bit_index: int) -> int:
        """
        Get specific bit from byte sequence.
        
        Args:
            data: Byte sequence
            bit_index: Index of bit to retrieve
            
        Returns:
            int: Bit value (0 or 1)
        """
        byte_index = bit_index // 8
        bit_offset = bit_index % 8
        return (data[byte_index] >> bit_offset) & 1