from jam.types.base.integers.fixed import U32

anti_log = [0] * 131072  # anti-log
log = [0] * 65536  # log

CANTOR_BASIS = [0x0001, 0xACCA, 0x3C0E, 0x163E, 0xC582, 0xED2E, 0x914C, 0x4012,
                    0x6C98, 0x10D8, 0x6A72, 0xB900, 0xFDB8, 0xFB34, 0xFF38, 0x991E]

class GF:
    @staticmethod
    def init_tables(prim: U32):
        global anti_log, log
        anti_log = [0] * 131072  # anti-log
        log = [0] * 65536  # log
        x = 1
        for i in range(0, 65535):
            anti_log[i] = x
            log[x] = i
            x = x<<1
            if x & 0x10000:
                x ^= prim

        for i in range(65535, 131072):
            anti_log[i] = anti_log[i - 65535]

        # Cantor basis transformation
        # temp_elements = [0] * 65536
        # for i in range(1, 65536):
        #     cantor_value = 0
        #     for bit in range(16):
        #         if i & (1 << bit):
        #             cantor_value ^= CANTOR_BASIS[bit]
        #     temp_elements[i] = cantor_value
        #
        # # Adjust tables
        # new_log = [0] * 65536
        # new_anti_log = [0] * 131072
        # new_log[0] = 0
        # for i in range(1, 65536):
        #     cantor_elem = temp_elements[i]
        #     new_log[cantor_elem] = i
        #     new_anti_log[i] = cantor_elem
        # new_anti_log[0] = 1
        # new_anti_log[65535] = 1
        # for i in range(65535, 131072):
        #     new_anti_log[i] = new_anti_log[i - 65535]
        #
        # return [new_log, new_anti_log]

        return [log, anti_log]

    # Arithmatic operations in GF
    @staticmethod
    def multiply(x,y):
        """
        multiplication using log and anti log
        log(a*b) = log(a) + log(b)
        a*b = anti_log(log(a*b))
        Args:
            x:
            y:
        Returns:
            x*y
        """
        if x==0 or y==0:
            return 0
        return anti_log[log[x] + log[y]]

    @staticmethod
    def div(x, y):
        """
        Division using log and anti log
        log(a/b) = log(a) - log(b)
        a/b = anti_log(log(a/b))
        Args:
            x:
            y:
        Returns:
            x/y
        """
        if y == 0:
            raise ZeroDivisionError()
        if x == 0:
            return 0
        return anti_log[(log[x] + 65535 - log[y]) % 65535]

    @staticmethod
    def inverse(x):
        """
        Inverse(x) = 1/x
        Args:
            x:
        Returns:
            1/x
        """
        return anti_log[65535 - log[x]]

    @staticmethod
    def pow(x, power):
        """
        Calculate x raise to power
        Args:
            x: Number
            power: Number
        Returns:
            x^power: Number
        """
        return anti_log[(log[x] * power) % 65535]

    # Polynomial Operations
    def poly_mul(self, p,q):
        """
        Multiplication of polynomial in Galois Field
        Args:
            p: List of coefficient of 1st polynomial
            q: List of coefficient of 2nd polynomial
        Returns:
            List of coefficient of resultant polynomial
        """
        r = [0] * (len(p)+len(q)-1)
        for j in range(0, len(q)):
            for i in range(0, len(p)):
                r[i+j] ^= self.multiply(p[i], q[j])
        return r

    # create a generator polynomial recursively
    def generator_poly(self, parity_symbol):
        """
        Generates an irreducible generator polynomial.

        Args:
            parity_symbol: Total number of parity symbols.
        Returns:
            Generator polynomial.
        """
        g = [1]
        for i in range(0, parity_symbol):
            g = self.poly_mul(g, [1, anti_log[i]])
        return g

    def poly_eval(self, polynomial, x):
        """
        Evaluates a polynomial in GF(2^p) given the value for x.
        Args:
            polynomial:
            x:
        Returns:
            Value of polynomial at x
        """
        y = polynomial[0]
        for i in range(1, len(polynomial)):
            y = self.multiply(y, x) ^ polynomial[i]
        return y

    @staticmethod
    def poly_add(p, q):
        """
        Addition of two polynomial
        Args:
            p: polynomial
            q: polynomial
        Returns:
            Addition of p & q
        """
        r = [0] * max(len(p), len(q))
        for i in range(0, len(p)):
            r[i + len(r) - len(p)] = p[i]
        for i in range(0, len(q)):
            r[i + len(r) - len(q)] ^= q[i]
        return r

    def poly_div(self, p, q):
        """
        Polynomial division using synthetic division in GF
        Args:
            p: Dividend
            q: Divisor
        Returns:
            p/q
        """
        msg_out = list(p)
        for i in range(0, len(p) - (len(q) - 1)):
            coefficient = msg_out[i]
            if coefficient != 0:
                for j in range(1, len(q)):
                    if q[j] != 0:
                        msg_out[i + j] ^= self.multiply(q[j], coefficient)
        separator = -(len(q) - 1)
        return msg_out[:separator], msg_out[separator:]

