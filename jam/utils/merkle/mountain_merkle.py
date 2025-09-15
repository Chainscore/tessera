from tsrkit_types.null import Null
from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from jam.types.protocol.crypto import OpaqueHash

from typing import Callable, Optional
from jam.types.protocol.crypto import Hash
from jam.types.protocol.merkle import MMR, OptionHash


class MMRFunctions:
    """General Merklization implementation for Merkle Mountain Ranges as defined in Section E.2"""

    def __init__(self):
        super().__init__()
        self._ZERO_HASH = OpaqueHash([0] * 32)
        self._PEAK_PREFIX = bytes("peak", "utf-8")
        self._NULL_VAL = OptionHash(Null)

    def _p(
        self,
        mmr: MMR,
        new_hash: Bytes[32],
        index: int,
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

        mmr_len = len(mmr)

        if index >= mmr_len:
            mmr.append(OptionHash(new_hash))

        else:
            val = mmr[index].unwrap()

            if val == Null:
                mmr[index] = OptionHash(new_hash)

            else:
                mmr[index] = self._NULL_VAL

                hash_dash = hash_fn(val + new_hash)

                mmr = self._p(mmr, hash_dash, index+1, hash_fn)

        return mmr

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

        return self._p(mmr, new_hash, 0, hash_fn)

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
            return Hash.keccak256(
                self._PEAK_PREFIX + val + bytes(h[-1].unwrap())
            )
