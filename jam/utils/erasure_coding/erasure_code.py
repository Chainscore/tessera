from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import Vector
from jam.utils.chainspec import chain_config
from jam.utils.constants import ec_original_shards, ec_recovery_shards, ec_piece_size
import tsrkit_rs

class ErasureCode:
    def __init__(self, total_shards: int | None = None):
        self.total_shards = int(total_shards or chain_config.num_validators)
        self.original_shards = ec_original_shards(self.total_shards)
        self.recovery_shards = ec_recovery_shards(self.total_shards)
        self.piece_size = ec_piece_size(self.total_shards)

    # TODO: Sync EC
    # Prior: https://graypaper.fluffylabs.dev/#/7e6ff6a/3f19003f1900?v=0.6.7
    # Posterior: https://graypaper.fluffylabs.dev/#/38c4e62/3f68003f6800?v=0.7.0
    # Changelog: https://github.com/gavofyork/graypaper/pull/429/files#diff-78584eb56cdef34f354d848f8d42b0f77980d693984265ebddd0f94f9c649f31

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
