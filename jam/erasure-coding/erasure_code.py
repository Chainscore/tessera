from jam.types import Bytes
from typing import List

class ErasureCode:

    @staticmethod
    def split(data: Bytes, k: int) -> List[Bytes]:
        """
        Use the split function to divide the large sequence, n into k equal-sized subsequences d_0,d_1,…,d_k-1,
        Example: For the Import DA system with 4_104 octets and k=6, split into six sequences of 684 octets each.
        If the data is not divisible by k, pad the data with zero bytes.
        https://graypaper.fluffylabs.dev/#/5f542d7/3c60003c7600

        Args:
            data: Bytes
            k: int

        Returns:
            list[Bytes]
        """
        if len(data) % k != 0:
            data = data + b'\x00' * (k - len(data) % k)
        return [data[i::k] for i in range(k)]
    
    @staticmethod
    def join(data: List[Bytes]) -> Bytes:
        """
        Use the join function to combine the k subsequences d_0,d_1,…,d_k-1 into a single sequence d.
        https://graypaper.fluffylabs.dev/#/5f542d7/3dd1003dde00

        Args:
            data: list[Bytes]

        Returns:
            Bytes
        """
        return b''.join(data)
