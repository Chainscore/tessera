"""Small typed structures used by the JAM fuzzer target.

This module keeps simple type definitions in one place. We avoid heavy
third-party typing dependencies here so the module is easy to read and
maintain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

# Keep binary alias for clarity in code that handles bytes blobs
Bytes = bytes


@dataclass(frozen=True)
class KeyVal:
    key: Bytes
    value: Bytes


@dataclass(frozen=True)
class SetStateData:
    header: object  # keep generic to avoid importing large header module here
    state: List[KeyVal]


SetState = list[SetStateData]

__all__ = ["Bytes", "KeyVal", "SetStateData", "SetState"]
