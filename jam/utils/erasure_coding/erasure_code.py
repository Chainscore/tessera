import math
import reed_solomon_leopard

from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import Vector

from jam.utils.chainspec import chain_config


class ErasureCode:
    def __init__(self):
        self.total_shards = chain_config.num_validators
        self.original_shards = chain_config.erasure_coding_original_shards
        self.recovery_shards = chain_config.erasure_coding_recovery_shards

    # TODO: Sync EC
    # Prior: https://graypaper.fluffylabs.dev/#/7e6ff6a/3f19003f1900?v=0.6.7
    # Posterior: https://graypaper.fluffylabs.dev/#/38c4e62/3f68003f6800?v=0.7.0
    # Changelog: https://github.com/gavofyork/graypaper/pull/429/files#diff-78584eb56cdef34f354d848f8d42b0f77980d693984265ebddd0f94f9c649f31

    @staticmethod
    def unzip(data: Bytes, k: int) -> Vector[Bytes]:
        """
        Use the unzip function to divide the array into k sequences d_0,d_1,…,d_k-1.
        https://graypaper.fluffylabs.dev/#/5f542d7/3ca7003cc900

        Args:
            data: Bytes
            k: Int

        Returns:
            List[Bytes]
        """
        return [data[i::k] for i in range(k)]

    def encode(self, data: Bytes) -> Vector[Bytes]:
        """
        Erasure-code chunking function
        Args:
            data: data blob
        Returns:
            1023 sequences of sequences
        """
        length = len(data)

        w_e = (2 * self.original_shards)

        # Data whose length is not divisible by w_e is padded with zero
        if length % w_e != 0:
            target_size = ((length // w_e) + 1) * w_e
            padding_size = target_size - length
            data = data + (b"\x00" * padding_size)

        bytes_per_chunk = math.ceil(len(data) / (2 * self.original_shards))
        octet_pairs = [data[i:i + 2] for i in range(0, len(data), 2)]

        # zero padding if octet pairs are not multiple of bytes_per_chunk
        length = len(octet_pairs)
        if length % bytes_per_chunk != 0:
            target_size = ((length // bytes_per_chunk) + 1) * bytes_per_chunk
            padding_size = target_size - length
            for i in range(padding_size):
                octet_pairs.append(b"00")

        # unzip
        p = self.unzip(octet_pairs, bytes_per_chunk)

        # reed solomon encoding
        for i in p:
            recovery = reed_solomon_leopard.encode(i, self.recovery_shards)
            i.extend(recovery)

        # transpose
        c = list(zip(*p))

        encoded_chunks = [b"".join(col) for col in c]

        return encoded_chunks

    def decode(self, c: Vector) -> Bytes:
        """
        Decoding function
        Args:
            c: List of chunks along with their index
        Returns:
            Decoded information
        """
        # split
        split_c = [
            [(chunk[j:j + 2], index) for j in range(0, len(chunk), 2)]
            for chunk, index in c
        ]

        # transpose
        transposed = [list(r) for r in zip(*split_c)]

        # reed solomon decoding
        for i in transposed:
            original_partial = {}
            recovery_partial = {}

            for chunk, index in i:
                if index < self.original_shards:
                    original_partial[index] = chunk
                else:
                    recovery_partial[index - self.original_shards] = chunk

            restored = reed_solomon_leopard.decode(
                self.original_shards,
                self.recovery_shards,
                original_partial,
                recovery_partial,
            )

            for key in restored:
                i.append((restored[key], key))

        # sorting decoded chunks
        sorted_decoded = [sorted(i, key=lambda x: x[1]) for i in transposed]

        decoded_data = b"".join(
            sorted_decoded[j][i][0]
            for i in range(self.original_shards)
            for j in range(len(sorted_decoded))
        )

        return decoded_data
