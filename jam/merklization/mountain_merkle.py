from jam.types import ByteArray32, decodable_option, OpaqueHash, Vector, Int, Null

T = TypeVar("T")

@decodable_option(element_type=OpaqueHash)
class OptionHash(Option): ...

@decodable_vector(element_type=OptionHash)
class MountainMerkle(Vector[OptionHash]):
    """General Merklization implementation for Merkle Mountain Ranges as defined in Section E.2"""

    # value: Vector[OptionHash]

    # def __init__(self, values: Vector[OptionHash]):
    def __init__(self):
        super().__init__()
        self._ZERO_HASH = ByteArray32([0] * 32)
        # self.value = values

    @staticmethod
    def _p(r: Vector[OptionHash], l: ByteArray32, n: Int, hash_fn: Optional[Hash]) -> Vector[OptionHash]:
        """Helper Function P Implementation as defined in Equation E.8"""

        r_len = Int(len(r))

        if n >= r_len:
            r += l
            return r

        elif n < r_len and r[n] is Null:
            return self._r(r, n, l)

        else:
            r_dash = self._r(r, n, Null)
            l_dash = hash_fn(r[n] + l)
            return self._p(r_dash, l_dash, n+1, hash_fn)

    @staticmethod
    def _r(seq: Vector[T], ind: Int, val: T) -> Vector[T]:
        """Helper Function R Implementation as defined in Equation E.8"""

        seq[ind] = val
        return seq

    def append_fn(self, r: Vector[OptionHash], l: ByteArray32, hash_fn: Optional[Hash]) -> Vector[OptionHash]:
        """Append Function Implementation as defined in Equation E.8"""

        if not hash_fn:
            hash_fn = Hash.blake2b

        return self._p(r, l, Int(0), hash_fn)

