from copy import deepcopy

from tsrkit_types.null import Null
from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from jam.types.protocol.crypto import OpaqueHash

from typing import Callable, TypeVar, Optional
from jam.types.protocol.crypto import Hash
from jam.types.protocol.merkle import MMR, OptionHash

T = TypeVar("T")


class MMRFunctions:
    """General Merklization implementation for Merkle Mountain Ranges as defined in Section E.2"""

    def __init__(self):
        super().__init__()
        self._ZERO_HASH = OpaqueHash([0] * 32)
        self._PEAK_PREFIX = bytes("peak", "utf-8")

    @staticmethod
    def _r(seq: TypedVector[T], ind: Uint, val: T) -> TypedVector[T]:
        """
        Helper Function R Implementation as defined in Equation E.8

        Definition:
            (s: [T], i: N, v: T) -> o: [T]
        Source:

        Args:
            seq: Generic Sequence
            ind: Index to update
            val: New Value
        Returns:
            Updated Sequence
        """

        seq_dash = deepcopy(seq)
        seq_dash[ind] = val
        return MMR(seq_dash)

    def _p(
        self,
        mmr: MMR,
        new_hash: Bytes[32],
        index: Uint,
        hash_fn: Optional[Callable[[bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> MMR:
        """
        Helper Function P Implementation as defined in Equation E.8

        Definition:
            (r: [H?], l: H, n: N, H: Y->H) -> o: [H?]
        Source:

        Args:
            mmr: Previous MMR Peaks
            new_hash: Hash to append
            index: Current step
            hash_fn: Hash Function
        Returns:
            Updated Mountain Merkle
        """

        mmr_len = Uint(len(mmr))

        if index >= mmr_len:
            mmr.append(OptionHash(new_hash))
            return mmr

        elif index < mmr_len and mmr[index] == OptionHash(Null):
            return self._r(mmr, index, OptionHash(new_hash))

        else:
            mmr_dagger = self._r(mmr, index, OptionHash(Null))
            mmr_dash = MMR(mmr_dagger)

            hash_dash = hash_fn(bytes(mmr[Uint(index)].unwrap()) + bytes(new_hash))

            return self._p(mmr_dash, hash_dash, Uint(index + 1), hash_fn)

    def append_fn(
        self,
        mmr: MMR,
        new_hash: Bytes[32],
        hash_fn: Optional[Callable[[bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> MMR:
        """
        Append Function Implementation as defined in Equation E.8

        Definition:
            (r: [H?], l: H, H: Y->H) -> o: [H?]
        Source:

        Args:
            mmr: Previous MMR Peaks
            new_hash: Hash to append
            hash_fn: Hash Function
        Returns:
            Updated Mountain Merkle
        """

        return self._p(mmr, new_hash, Uint(0), hash_fn)

    @staticmethod
    def encode_mmr(mmr: MMR) -> bytes:
        """
        MMR Encoding Function Implementation as defined in Equation E.9

        Definition:
            (mmr: [H?]) -> o: Y
        Source:

        Args:
            mmr: MMR Peaks
        Returns:
            Encoded Root
        """

        return mmr.encode()

    def super_peak(self, mmr: MMR, flag=True) -> OpaqueHash:
        """
        MMR Super Peak Function Implementation as defined in Equation E.10

        Definition:
            (mmr: [H?]) -> o: H
        Source:

        Args:
            mmr: MMR Peaks
            flag: Boolean
        Returns:
            Encoded Root
        """
        h = []

        if flag:
            for peak in mmr:
                if peak != OptionHash(Null):
                    h.append(peak)
        else:
            h = mmr

        if len(h) == 0:
            return self._ZERO_HASH

        elif len(h) == 1:
            return h[0].unwrap()

        else:
            val = self.super_peak(MMR(h[:-1]), False)
            return Hash.keccak256(self._PEAK_PREFIX + bytes(val) + bytes(h[-1].unwrap()))
