
from jam.ring_vrf.ring_proof.constants import S_PRIME
from sympy import Poly,symbols


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









