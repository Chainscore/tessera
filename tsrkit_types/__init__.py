"""
Light-weight stub of the `tsrkit_types` package.

The real `tsrkit_types` package provides strongly-typed wrappers and
serialization helpers that are not required for logic tests executed
inside this repository.  To keep the runtime self-contained while still
accepting the same public interface, we provide minimal shims that cover
only the functionality actually used by the codebase.

This stub purposefully keeps the implementation *very* thin – it should
**not** be relied upon for production use, cryptography, or binary
compatibility.  It merely allows the rest of the project to import the
expected symbols without bundling the external dependency.
"""

from __future__ import annotations

import sys
import types
from typing import Generic, TypeVar, Any, overload, Iterator

__all__ = [
    "Bytes",
    "Option",
    "Null",
    "U32",
    "U64",
]

_T = TypeVar("_T")


class Bytes(bytes, Generic[_T]):
    """Simple fixed-length byte wrapper.

    The generic parameter that encodes the expected length is **ignored** at
    runtime; it exists solely so that `Bytes[32]` etc. remain valid type
    annotations.  Length checks can still be performed explicitly by the
    caller if desired.
    """

    def __new__(cls, value: bytes | bytearray | "Bytes[_T]") -> "Bytes[_T]":
        if isinstance(value, (bytes, bytearray)):
            return bytes.__new__(cls, value)  # type: ignore[misc]
        # Accept constructing Bytes from another Bytes instance
        return bytes.__new__(cls, bytes(value))  # type: ignore[misc]

    # Allow `Bytes[32]` etc.
    @classmethod  # type: ignore[override]
    def __class_getitem__(cls, _size: Any):  # noqa: D401, ANN401
        return cls


class Option(Generic[_T]):
    """Very small substitute for a Rust-style `Option` type."""

    __slots__ = ("_value",)

    def __init__(self, value: _T | None):
        self._value = value

    def is_some(self) -> bool:  # noqa: D401
        return self._value is not None

    def is_none(self) -> bool:  # noqa: D401
        return self._value is None

    def unwrap(self) -> _T:
        if self.is_none():  # pragma: no cover – mimic Rust panic.
            raise ValueError("Called unwrap on a Null Option")
        return self._value  # type: ignore[return-value]

    # Enable pattern like `for x in option` to iterate over zero/one value.
    def __iter__(self) -> Iterator[_T]:
        if self.is_some():  # pragma: no branch
            yield self._value  # type: ignore[misc]

    def __repr__(self) -> str:  # noqa: D401
        return f"Option({self._value!r})"


Null: None = None  # Sentinel used by the codebase.


class _UInt(int):
    """Base class for little-endian encoded unsigned ints used in codecs."""

    num_bytes: int  # to be set by subclasses

    def encode(self) -> bytes:  # noqa: D401
        return int(self).to_bytes(self.num_bytes, "little")

    # The real API returns a tuple `(value, rest)` – we mimic that.
    @classmethod
    def decode_from(cls, data: bytes) -> tuple["_UInt", bytes]:
        if len(data) < cls.num_bytes:  # pragma: no cover – sanity guard.
            raise ValueError("Insufficient bytes to decode")
        value_bytes, rest = data[: cls.num_bytes], data[cls.num_bytes :]
        return cls(int.from_bytes(value_bytes, "little")), rest  # type: ignore[call-arg]


class U32(_UInt):
    num_bytes = 4


class U64(_UInt):
    num_bytes = 8


# ---------------------------------------------------------------------------
# Sub-modules – created dynamically so that `from tsrkit_types.bytes import
# Bytes` etc. work exactly the same way as with the real package.
# ---------------------------------------------------------------------------

_sub_modules: dict[str, types.ModuleType] = {}


def _register_submodule(name: str, public_attrs: dict[str, Any]) -> None:  # noqa: ANN401
    mod = types.ModuleType(name)
    mod.__dict__.update(public_attrs)
    sys.modules[name] = mod
    _sub_modules[name] = mod


# tsrkit_types.bytes ---------------------------------------------------------
_register_submodule(__name__ + ".bytes", {"Bytes": Bytes})

# tsrkit_types.sequences ------------------------------------------------------
class _TypedBoundedVector(list):
    """Placeholder – acts exactly like a list at runtime."""

    @classmethod
    def __class_getitem__(cls, _params: Any):  # noqa: D401, ANN401
        return list


_register_submodule(__name__ + ".sequences", {"TypedBoundedVector": _TypedBoundedVector,
                                                "TypedArray": list,
                                                "TypedVector": list,
                                                "Vector": list})

# tsrkit_types.struct ---------------------------------------------------------


def structure(cls):  # noqa: D401
    """No-op replacement for the real `@structure` decorator."""

    return cls


_register_submodule(__name__ + ".struct", {"structure": structure})

# tsrkit_types.enum -----------------------------------------------------------

class _Enum(int):
    """Extremely light replacement for the `Enum` helper used in the codebase."""

    def __new__(cls, value=0, *args, **kwargs):  # noqa: ANN001
        return int.__new__(cls, value)

    def __init_subclass__(cls, **kwargs):  # noqa: D401
        # Allow subclassing without additional behaviour.
        super().__init_subclass__(**kwargs)

    def __class_getitem__(cls, _params):  # noqa: D401, ANN401
        return cls


_register_submodule(__name__ + ".enum", {"Enum": _Enum})

# tsrkit_types.integers --------------------------------------------------------

class _Uint(int):
    """Generic unsigned integer placeholder."""

    def __class_getitem__(cls, _size):  # noqa: D401, ANN401
        return cls

    def encode(self) -> bytes:  # noqa: D401
        # Minimal helper similar to U32/U64.
        byte_length = (int(self).bit_length() + 7) // 8 or 1
        return int(self).to_bytes(byte_length, "little")


class _U16(_UInt):
    num_bytes = 2


class _U32(_UInt):
    num_bytes = 4


class _U64(_UInt):
    num_bytes = 8

# extend integers submodule export list
_register_submodule(__name__ + ".integers", {"Uint": _Uint, "U8": _Uint, "U16": _U16, "U32": _U32, "U64": _U64})

# tsrkit_types.option -----------------------------------------------------------
_register_submodule(__name__ + ".option", {"Option": Option})

# tsrkit_types.choice -----------------------------------------------------------
_register_submodule(__name__ + ".choice", {"Choice": _Enum})

__all__.extend(["TypedArray", "TypedVector", "structure", "Uint", "U8", "Dictionary", "U16"])

# Re-export top-level shortcuts ------------------------------------------------
TypedArray = list  # type: ignore
TypedVector = list  # type: ignore
structure = structure  # noqa: F821  – re-use the function defined above
Uint = _Uint
U8 = _Uint
Dictionary = dict  # type: ignore
U16 = _U16
U32 = _U32
U64 = _U64

class _NullType:
    """Singleton representing a Null value (akin to Rust's None)."""

    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "Null"

# Singleton instance
Null = _NullType()

_register_submodule(__name__ + ".null", {"NullType": _NullType, "Null": Null})

_register_submodule(__name__ + ".bool", {"Bool": bool})

__all__.append("Bool")
Bool = bool

class _Bits(int):
    def __class_getitem__(cls, _params):  # noqa: D401, ANN401
        return cls

_register_submodule(__name__ + ".bits", {"Bits": _Bits})

Bits = _Bits

_register_submodule(__name__ + ".dictionary", {"Dictionary": dict})
