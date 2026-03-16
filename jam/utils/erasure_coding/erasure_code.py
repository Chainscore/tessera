from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import Vector
from jam.utils.chainspec import chain_config
import tsrkit_rs

class ErasureCode:
    def __init__(self):
        self.total_shards = chain_config.num_validators
        self.original_shards = chain_config.erasure_coding_original_shards
        self.recovery_shards = chain_config.erasure_coding_recovery_shards

    def encode(self, data: Bytes) -> Vector[Bytes]:
        """
        Erasure-code chunking function
        Args:
            data: data blob
        Returns:
            1023 sequences of sequences
        """
        return tsrkit_rs.encode_py(data, self.original_shards, self.recovery_shards)

    def encode_multiple_segments(self, data: Bytes) -> Vector[Bytes]:
        """
        Erasure-code chunking function which accepts an array of segments
        Args:
            data: data blob
        Returns:
            sequences of 1023 sequences
        """
        return tsrkit_rs.multi_encode_py(data, self.original_shards, self.recovery_shards)

    def decode(self, c: Vector) -> Bytes:
        """
        Decoding function
        Args:
            c: List of chunks along with their index
        Returns:
            Decoded information
        """
        return tsrkit_rs.decode_py(c, self.original_shards, self.recovery_shards)
