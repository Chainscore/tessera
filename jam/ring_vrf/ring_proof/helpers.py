from py_ecc.bls import point_compression
from py_ecc.optimized_bls12_381 import FQ, is_on_curve, G1

from jam.ring_vrf.ring_proof.constants import S_PRIME


def knocker_delta(i,j):
    """"
    input:i,j
    output: return 1 if i==j 0 otherwise
    """
    return 1 if i==j else 0

def unzip(points):
    """"
    input:Gets a list of points as input
    output:Splits the points into x,y co-ordinates
    """
    x_c=[pt[0] for pt in points]
    y_c=[pt[1] for pt in points]
    return x_c,y_c


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

#bls point to string
def bls_g1_compress(bls_point):
    if len(bls_point)==2:
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


#bls string to point
def bls_g1_decompress(byte_array):
    dcp_scalar=int(byte_array,16)
    decompressed = point_compression.decompress_G1(dcp_scalar)
    assert is_on_curve(decompressed,4), "INVALID POINT"
    return decompressed

#
# def main():
#     b_c=(1332310689855977281988073361583473861448181703578082464893324255082586328540004758008760342419545320465710360446231, 1083094159812582322688886646243817038393280166989720523735466912565067215129958786830520140761135404613535398368005)
#
#     cp=bls_g1_compress(b_c)
#     print(cp)
#     print(bls_g1_decompress(cp))

# if __name__=="__main__":
#     main()







