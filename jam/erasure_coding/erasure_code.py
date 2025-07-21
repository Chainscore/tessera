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

    @staticmethod
    def unzip(data: Bytes, n: int, k: int) -> Vector[Bytes]:
        """
        Use the unzip function to divide the array into k sequences d_0,d_1,…,d_k-1.
        https://graypaper.fluffylabs.dev/#/5f542d7/3ca7003cc900

        Args:
            data: Bytes
            n: Int
            k: Int

        Returns:
            List[Bytes]
        """
        res = Vector([])
        for i in range(0, k):
            temp = Vector([])
            for j in range(0, n):
                temp.append(data[(j * k) + i])
            res.append(temp)

        return res

    def encode(self, data: bytes) -> Vector[bytes]:
        """
        Erasure-code chunking function
        Args:
            data: data blob
        Returns:
            1023 sequences of sequences
        """
        length = len(data)
        # Data whose length is not divisible by 684 is padded with zero
        if length % 684 != 0:
            target_size = ((length // 684) + 1) * 684
            padding_size = target_size - length
            data = data + (b"\x00" * padding_size)

        bytes_per_chunk = math.ceil(len(data) / (2 * self.original_shards))
        octet_pairs = []
        for i in range(0, len(data), 2):
            resultant = bytes(b for b in data[i : i + 2])
            octet_pairs.append(resultant)

        # zero padding if octet pairs are not multiple of bytes_per_chunk
        length = len(octet_pairs)
        if length % bytes_per_chunk != 0:
            target_size = ((length // bytes_per_chunk) + 1) * bytes_per_chunk
            padding_size = target_size - length
            for i in range(padding_size):
                octet_pairs.append(b"00")

        # unzip
        p = self.unzip(octet_pairs, self.original_shards, bytes_per_chunk)

        # reed solomon encoding
        for i in p:
            recovery = reed_solomon_leopard.encode(i, self.recovery_shards)
            i.extend(recovery)

        # transpose
        c = [[p[j][i] for j in range(len(p))] for i in range(len(p[0]))]

        encoded_chunks = Vector([])
        for i in range(0, len(c)):
            res_str = b""
            for j in range(0, bytes_per_chunk):
                res_str += c[i][j]
            encoded_chunks.append(res_str)

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
        split_c = []
        for i in c:
            chunk = i[0]
            index = i[1]
            symbols = []
            for j in range(0, len(chunk), 2):
                symbols.append((chunk[j : j + 2], index))
            split_c.append(symbols)

        # transpose
        transposed = [
            [split_c[j][i] for j in range(len(split_c))] for i in range(len(split_c[0]))
        ]

        # reed solomon decoding
        for i in transposed:
            original_partial = {}
            recovery_partial = {}

            for msg in i:
                index = msg[1]
                chunk = msg[0]
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
        sorted_decoded = []
        for i in transposed:
            sorted_list = sorted(i, key=lambda x: x[1])
            sorted_decoded.append(sorted_list)

        decoded_data = b""
        for i in range(self.original_shards):
            for j in range(len(sorted_decoded)):
                decoded_data += sorted_decoded[j][i][0]

        return decoded_data
