from typing import List
from jam.erasure_coding.error import ErasureCodingErrorCode, ErasureCodingError
from jam.erasure_coding.galois_field import GF


class ErasureCode(GF):

    def __init__(self):
        self.init_tables(0x1002D)

    @staticmethod
    def unzip(data: List[int], n: int, k: int):
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

        res = []
        for i in range(0, k):
            temp = []
            for j in range(0, n):
                temp.append(data[(j * k) + i])
            res.append(temp)

        return res

    def encode_msg(self, input, paritySym):
        """
        Reed solomon encoding function
        Args:
            input:
            paritySym:
        Returns:
            input+parity_bits
        """
        gen = self.generator_poly(paritySym)
        output = [0] * (len(input) + len(gen)-1)
        output[:len(input)] = input

        for i in range(len(input)):
            coefficient = output[i]
            if coefficient != 0:
                for j in range(1, len(gen)):
                    output[i+j] ^= self.multiply(gen[j], coefficient) # in GF addition is equivalent to xor

        output[:len(input)] = input

        return output

    def syndrome_calculation(self, msg, nsym):
        """
        Calculate syndromes polynomial based on message and error correcting symbols.
        Args:
            msg:
            nsym: number parity bits
        Returns:
            Syndromes polynomial
        """
        synd = [0] * nsym
        for i in range(0, nsym):
            synd[i] = self.poly_eval(msg, self.pow(2,i))
        return [0] + synd

    def find_error_locator_poly(self, erasure_pos):
        """
        Calculate error/erasure locator polynomial from given positions
        Args:
            erasure_pos: Erasure positions
        Returns:
            Erasure locator polynomial
        """
        e_loc = [1]
        for i in erasure_pos:
            e_loc = self.poly_mul( e_loc, self.poly_add([1], [self.pow(2, i), 0]) )
        return e_loc


    def find_error_evaluator_poly(self, synd, err_loc, nsym):
        """
        calculate error evaluator polynomial using Erasure locator polynomial & Syndromes
        Args:
            synd: syndromes
            err_loc: Erasure locator polynomial
            nsym: Number of parity bits
        Returns:
            Error evaluator polynomial
        """
        _, remainder = self.poly_div( self.poly_mul(synd, err_loc), ([1] + [0]*(nsym+1)) )
        return remainder

    def erasure_correction(self, msg_in, synd, err_pos):
        """
        Forney's algorithm to calculate the values of erasure
        Args:
            err_pos: Erasure positions
            msg_in: input message
            synd: error syndrome
        """
        coef_pos = [len(msg_in) - 1 - p for p in err_pos]
        err_loc = self.find_error_locator_poly(coef_pos)
        err_eval = self.find_error_evaluator_poly(synd[::-1], err_loc, len(err_loc) - 1)[::-1]

        X = []
        for i in range(0, len(coef_pos)):
            l = 65535 - coef_pos[i]
            X.append(self.pow(2, -l))

        E = [0] * (len(msg_in))
        Xlength = len(X)
        for i, Xi in enumerate(X):
            Xi_inv = self.inverse(Xi)
            err_loc_prime_tmp = []
            for j in range(0, Xlength):
                if j != i:
                    err_loc_prime_tmp.append((1^self.multiply(Xi_inv, X[j])))
            err_loc_prime = 1
            for coef in err_loc_prime_tmp:
                err_loc_prime = self.multiply(err_loc_prime, coef)
            y = self.poly_eval(err_eval[::-1], Xi_inv)
            y = self.multiply(self.pow(Xi, 1), y)

            if err_loc_prime == 0:
                raise ErasureCodingError(ErasureCodingErrorCode.BAD_ERASURE , "Could not find error magnitude")

            magnitude = self.div(y, err_loc_prime)
            E[err_pos[i]] = magnitude

        msg_in = self.poly_add(msg_in, E)
        return msg_in

    def decode_msg(self, msg_in, nsym, erasure_pos=None):
        """
        Reed solomon decoding function
        Args:
            msg_in: message received
            nsym: number of parity bits
            erasure_pos: erasure position
        """
        if len(msg_in) > 65535:
            raise ErasureCodingError(ErasureCodingErrorCode.BAD_IMPORT_MESSAGE , "Message is too long")

        msg_out = list(msg_in)

        # cannot correct erasure greater than 681
        if len(erasure_pos) > nsym: raise ErasureCodingError(ErasureCodingErrorCode.BAD_ERASURE, "Too many erasures to correct")
        # prepare the syndrome polynomial
        synd = self.syndrome_calculation(msg_out, nsym)

        if max(synd) == 0:
            return msg_out

        msg_out = self.erasure_correction(msg_out, synd, erasure_pos)

        synd = self.syndrome_calculation(msg_out, nsym)

        if max(synd) > 0:
            raise ErasureCodingError(ErasureCodingErrorCode.BAD_MESSAGE, "Could not correct message")

        return msg_out

    def encode(self, data):
        """
        Erasure-code chunking function
        Args:
            data: data blob
        Returns:
            1023 sequences of sequences
        """
        length = len(data)

        if length % 684 != 0:
            target_size = ((length // 684) + 1) * 684
            padding_size = target_size - length
            data = data + (b'\x00' * padding_size)

        octet_pairs = []
        for i in range(0, len(data), 2):
            resultant = int.from_bytes(bytes(int(b) for b in data[i:i + 2]), 'little')
            octet_pairs.append(resultant)

        k = len(octet_pairs) // 342
        res = self.unzip(octet_pairs, 342, k)

        op = []
        for i in res:
            msg = self.encode_msg(i, 681)
            op.append(msg)

        transposed = [[op[j][i] for j in range(len(op))] for i in range(len(op[0]))]

        encodedChunks = []
        for i in range(0, len(transposed)):
            resStr = ''
            for j in range(0, k):
                resStr += transposed[i][j].to_bytes(2, byteorder='little').hex()
            encodedChunks.append(resStr)

        return encodedChunks

    def decode(self, c):
        """
        Decoding function
        Args:
            c: List of chunks along with their index
        Returns:
            Decoded information
        """
        k = len(c[0][0]) // 2
        erasure_pos = []
        present_pos = []
        for msg in c:
            index = msg[1]
            present_pos.append(index)

        for i in range(1023):
            if i not in present_pos:
                erasure_pos.append(i)

        # using b'00'*k as placeholder for erasure
        new_c = [b'00' * k] * 1023

        for msg in c:
            index = msg[1]
            chunk = msg[0]
            new_c[index] = chunk

        decoded = []
        for i in range(0, 1023):
            chunk = new_c[i]
            symbols = []
            for j in range(0, len(chunk), 2):
                symbols.append(int.from_bytes(chunk[j:j + 2], 'little'))
            decoded.append(symbols)

        decoded_transposed = [[decoded[j][i] for j in range(len(decoded))] for i in range(len(decoded[0]))]

        final_decoded = []
        for i in decoded_transposed:
            decoded = self.decode_msg(i, 681, erasure_pos)
            final_decoded.append(decoded)

        transposed = [[final_decoded[j][i] for j in range(len(final_decoded))] for i in range(len(final_decoded[0]))]

        decoded_chunks = []
        for i in range(0, len(transposed)):
            resStr = ''
            for j in range(0, k):
                resStr += transposed[i][j].to_bytes(2, byteorder='little').hex()
            decoded_chunks.append(resStr)

        decoded_data = ""
        for i in range(342):
            decoded_data += decoded_chunks[i]

        return decoded_data
