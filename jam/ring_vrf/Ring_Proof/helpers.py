from py_ecc.bls import point_compression
from py_ecc.optimized_bls12_381 import FQ, is_on_curve

from jam.ring_vrf.Ring_Proof.constants import S_PRIME

class Helpers:

    @staticmethod
    def knocker_delta(i, j):
        """"
        input:i,j
        output: return 1 if i==j 0 otherwise
        """
        return 1 if i == j else 0

    @staticmethod
    def unzip(points):
        """"
        input:Gets a list of points as input
        output:Splits the points into x,y co-ordinates
        """
        x_c = [pt[0] for pt in points]
        y_c = [pt[1] for pt in points]
        return x_c, y_c

    @staticmethod
    def do_modulus(poly):

        # Expand the polynomial to ensure all terms are explicitly separated
        expanded_poly = poly

        # Extract all terms and their coefficients
        coeff_dict = expanded_poly.as_coefficients_dict()

        # Apply modulus to all coefficients
        coeff_mod = {term: coeff % S_PRIME for term, coeff in coeff_dict.items()}

        # Reconstruct the polynomial
        poly_mod = sum(coeff * term for term, coeff in coeff_mod.items())

        return poly_mod

    @staticmethod
    # bls point to string
    def bls_g1_compress(bls_point):
        if len(bls_point) == 2:
            point = (
                FQ(bls_point[0]),
                FQ(bls_point[1]),
                FQ(1))
        else:
            point = (
                FQ(bls_point[0]),
                FQ(bls_point[1]),
                FQ(bls_point[2]))

        # Compress the point
        compressed = point_compression.compress_G1(point)
        hex_rep = compressed.to_bytes(48, 'big').hex()
        return hex_rep

    @staticmethod
    # bls string to point
    def bls_g1_decompress(byte_array):
        dcp_scalar = int(byte_array, 16)
        decompressed = point_compression.decompress_G1(dcp_scalar)
        assert is_on_curve(decompressed, 4), "INVALID POINT"
        return decompressed

    @staticmethod
    # for fiat_shamir
    def to_int(tup):
        x, y = tup
        res = int(x), int(y)
        return res

    @staticmethod
    # int to hex_string
    def to_bytes(val):
        res = val.to_bytes(32, 'little')
        return res.hex()

    @staticmethod
    def altered_points(g2_points):
        res= [(b, a) for pair in g2_points for point in pair for a, b in [point]]
        return res

