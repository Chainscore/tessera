
from jam.ring_vrf.ring_proof.constants import S_PRIME, D
from sympy import  symbols, expand,Poly
from sympy import symbols
x=symbols('x')
import numpy as np

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


#vector subtraction
def vect_sub(a,b, prime):
    if isinstance(a, int) and isinstance(b, list):
        n=len(b)
        a=[a]*n
        result=[(i-j)%prime for i,j in zip(a,b)]
        return result
    elif isinstance(a,list) and isinstance(b, int):
        n=len(a)
        b=[b]*n
        result= [(i-j)% prime for i, j in zip(a,b)]
        return result
    else:
        result=[(i-j)%prime for i, j in zip(a,b)]
        return result


#vector adddition

def vect_add(a, b, prime):
    if isinstance(a, int) and isinstance(b, list):
        n=len(b)
        a=[a]*n
        result=[(i+j)%prime for i,j in zip(a,b)]
        return result
    elif isinstance(a,list) and isinstance(b, int):
        n=len(a)
        b=[b]*n
        result= [(i+j)% prime for i, j in zip(a,b)]
        return result
    else:
        result=[(i+j)%prime for i, j in zip(a,b)]
        return result

#vector multiplictaion

def vect_mul(a, b, prime):
    if isinstance(a, int) and isinstance(b, list):
        n=len(b)
        a=[a]*n
        result=[(i*j)%prime for i,j in zip(a,b)]
        return result
    elif isinstance(a,list) and isinstance(b, int):
        n=len(a)
        b=[b]*n
        result= [(i*j)% prime for i, j in zip(a,b)]
        return result
    else:
        result=[(i*j)%prime for i, j in zip(a,b)]
        return result

def vect_scalar_mul(vec, scalar, mod=None):
    """Multiply each element in the vector by the scalar"""
    return [(x * scalar) % mod if mod else x * scalar for x in vec]

