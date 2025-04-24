######
from jam.ring_vrf.ring_proof.constants import S_PRIME, D
from sympy import  symbols, expand,Poly
import numpy as np


##initail
# def polynomial_interpolation(x_coords, y_coords):
#     """
#         input: list of points
#         output: A ploynomial passing through the given list of points
#         Resources:https://en.wikipedia.org/wiki/Lagrange_polynomial,
#         https://www.youtube.com/watch?v=F5pJG422781213702924172180523978385542388841346373992886390990881355510284839737428YfQxs
#     """
#     x = symbols('x')
#     lagranges_x = []
#
#     for i in range(len(y_coords)):
#         # l_x[i]= Phi(X-Xj / (Xi-Xj))... (& i!=j)
#         l_x = 1
#         for j in range(len(y_coords)):
#             if i != j:
#                 denominator = x_coords[i] - x_coords[j]
#                 if denominator == 0:
#                     raise ValueError("Duplicate x-values detected, interpolation is undefined.")
#
#                 # Modular inverse within finite  field
#                 denom_inv = mod_inverse(denominator, S_PRIME)
#                 l_x *= (x - x_coords[j]) * denom_inv % S_PRIME
#
#         lagranges_x.append(l_x)
#     # construct the final polynomial
#     # P(x) =∑YiLi(X)
#     polynomial = 0
#     for i in range(0, len(y_coords)):
#         polynomial += y_coords[i] * lagranges_x[i] % S_PRIME
#     return expand(polynomial) %S_PRIME

# def check_is_valid(interpolated_poly,D,p_v):
#     """
#     """
#     x = symbols('x')
#     for i in range(len(D)):
#         evaluated = interpolated_poly.subs(x, D[i]) % S_PRIME
#         # print("for py1")
#         # print(f"Evaluated_Y: {evaluated}, Expected_Y: {p_v[i] % S_PRIME}")
#         assert evaluated == (p_v[i] % S_PRIME), "Invalid Polynomial"
#     return True


# def interpolated_poly_at_index(idx,interpolated_poly,D,p_v):
#     x= symbols('x')
#
#     evaluated = interpolated_poly.subs(x, D[idx]) % S_PRIME
#     assert evaluated == (p_v[idx] % S_PRIME), "Invalid Polynomial"
#     return evaluated

def selector_vector(size=512):
    """
    input: ring of public key's
    output: selecting vector having 0/1
    """
    s_vector = []
    N_K=255 #len(Ring_of_pk)

    for i in range(size):
        if i<N_K:
            s_vector.append(1)
        else:
            s_vector.append(0)

    return s_vector

## Up Dated ##

def mod_inverse(val, prime):
    """Find the modular multiplicative inverse of a under modulo m."""
    if pow(val, prime - 1, prime) != 1:
        raise ValueError("No inverse exists")
    return pow(val, prime - 2, prime)



def poly_add(poly1, poly2, prime):
    """Add two polynomials in a prime field."""
    # Make them the same length
    result_len = max(len(poly1), len(poly2))
    result = [0] * result_len

    for i in range(len(poly1)):
        result[i] = poly1[i]

    for i in range(len(poly2)):
        result[i] = (result[i] + poly2[i]) % prime

    # Remove trailing zeros
    # while result and result[-1] == 0 and len(result) > 1:
    #     result.pop()
    return result


def poly_subtract(poly1, poly2, prime):
    """Subtract poly2 from poly1 in a prime field."""
    # Make them the same length
    result_len = max(len(poly1), len(poly2))
    result = [0] * result_len

    for i in range(len(poly1)):
        result[i] = poly1[i]

    for i in range(len(poly2)):
        result[i] = (result[i] - poly2[i]) % prime

    # Remove trailing zeros
    # while result and result[-1] == 0 and len(result) > 1:
    #     result.pop()

    return result



#(O^2) initial
def poly_multiply(poly1, poly2, prime):
    """Multiply two polynomials in a prime field."""
    result_len = len(poly1) + len(poly2) - 1
    result = [0] * result_len
    for i in range(len(poly1)):
        for j in range(len(poly2)):
            result[i + j] = (result[i + j] + poly1[i] * poly2[j]) % prime

    # Remove trailing zeros
    # while result and result[-1] == 0 and len(result) > 1:
    #     result.pop()
    return result


#fft

# def fft_poly_mul(A, B, omega_root, p):
#     size = next_power_of_2(len(A) + len(B) - 1)
#
#     # Pointwise multiplication
#     C_vals = [(a * b) % p for a, b in zip(A, B)]
#     # Optional: trim trailing 0s



def poly_scalar(poly, scalar, prime):
    """Multiply a polynomial by a scalar in a prime field."""
    result = [(coef * scalar) % prime for coef in poly]

    # Remove trailing zeros
    # while result and result[-1] == 0 and len(result) > 1:
    #     result.pop()

    return result


def poly_evaluate(poly, x, prime):
    """Evaluate a polynomial at point x using Horner's method."""
    result = 0
    for coef in  reversed(poly):
        result = (result * x + coef) % prime
    return result


def polynomial_interpolation(x_coords, y_coords, prime=S_PRIME):
    """
    Perform Lagrange polynomial interpolation over a prime field.

    Args:
        x_coords: List of x coordinates
        y_coords: List of y coordinates
        prime: The prime modulus for the field (defaults to S_PRIME)

    Returns:
        List of coefficients representing the interpolated polynomial
    """
    n = len(x_coords)
    result = [0]  # Start with polynomial 0

    for i in range(n):
        # Compute i-th Lagrange basis polynomial
        basis_poly = lagrange_basis_polynomial(x_coords, i, prime)

        # Scale it by y_i
        scaled_basis = poly_scalar(basis_poly, y_coords[i], prime)

        # Add to the result
        result = poly_add(result, scaled_basis, prime)

    return result

def lagrange_basis_polynomial(x_coords, i, prime=S_PRIME):
    """
    Compute the i-th Lagrange basis polynomial.

    L_i(x) = (x - x_j) / (x_i - x_j)
    """
    n = len(x_coords)
    numerator = [1]  # Start with polynomial 1
    denominator = 1

    for j in range(n):
        if j != i:
            # Multiply numerator by (x - x_j)
            term = [(-x_coords[j]) % prime, 1]
            numerator = poly_multiply(numerator, term, prime)

            # Multiply denominator by (x_i - x_j)
            diff = (x_coords[i] - x_coords[j]) % prime
            denominator = (denominator * diff) % prime

    # Calculate modular inverse of denominator
    inv_denominator = mod_inverse(denominator, prime)

    # Scale the numerator polynomial
    basis_poly = poly_scalar(numerator, inv_denominator, prime)

    return basis_poly




def represent_as_poly(coeffs):
    x = symbols('x')
    n = len(coeffs)
    coeffs=coeffs[::-1]
    # Create the polynomial with all terms, including zeros
    polynomial = sum(coeff * x ** (n - 1 - i) for i, coeff in enumerate(coeffs))

    return polynomial

from sympy import symbols
x=symbols('x')

L_0_x = lagrange_basis_polynomial(D, 0)

# print("is 1:",represent_as_poly(L_0_x).subs(x,D[0]))
L_N_4_x = lagrange_basis_polynomial(D, 512 - 4)
p2=represent_as_poly(L_N_4_x)
p1=represent_as_poly(L_0_x)

print(L_0_x)
print(L_N_4_x)
print(p1)
print(p1.subs(x,D[0])%S_PRIME)
print(p2.subs(x,D[0])%S_PRIME)
print(p1.subs(x,D[-4])%S_PRIME)
print(p2.subs(x,D[-4])%S_PRIME)


# import time
# def main():
#     start=time.time()
#     x_cord = D
#     y_cord = selector_vector()
#     coeff_poly = polynomial_interpolation(x_cord, y_cord, S_PRIME)
#     print(represent_as_poly(coeff_poly))
#     end=time.time()
#     print(end-start)
#
#
# if __name__=="__main__":
#     main()

