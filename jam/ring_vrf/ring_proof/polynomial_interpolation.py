from sympy import symbols, mod_inverse, expand
from jam.ring_vrf.ring_proof.constants import  S_PRIME



def polynomial_interpolation(x_coords, y_coords):
    """
        input: list of points
        output: A ploynomial passing through the given list of points
        Resources:https://en.wikipedia.org/wiki/Lagrange_polynomial,
        https://www.youtube.com/watch?v=F5pJG422781213702924172180523978385542388841346373992886390990881355510284839737428YfQxs
    """
    x = symbols('x')
    lagranges_x = []

    for i in range(len(y_coords)):
        # l_x[i]= Phi(X-Xj / (Xi-Xj))... (& i!=j)
        l_x = 1
        for j in range(len(y_coords)):
            if i != j:
                denominator = x_coords[i] - x_coords[j]
                if denominator == 0:
                    raise ValueError("Duplicate x-values detected, interpolation is undefined.")

                # Modular inverse within finite field
                denom_inv = mod_inverse(denominator, S_PRIME)
                l_x *= (x - x_coords[j]) * denom_inv

        lagranges_x.append(l_x)

    #construct the final polynomial
    # P(x) =∑YiLi(X)
    polynomial = 0
    for i in range(0, len(y_coords)):
        polynomial += y_coords[i] * lagranges_x[i]

    return expand(polynomial)


def check_is_valid(interpolated_poly,D,p_v):
    """
    """
    x = symbols('x')
    for i in range(len(D)):
        evaluated = interpolated_poly.subs(x, D[i]) % S_PRIME
        # print("for py1")
        # print(f"Evaluated_Y: {evaluated}, Expected_Y: {p_v[i] % S_PRIME}")
        assert evaluated == (p_v[i] % S_PRIME), "Invalid Polynomial"
    return True


def interpolated_poly_at_index(idx,interpolated_poly,D,p_v):
    x= symbols('x')

    evaluated = interpolated_poly.subs(x, D[idx]) % S_PRIME
    assert evaluated == (p_v[idx] % S_PRIME), "Invalid Polynomial"
    return evaluated















