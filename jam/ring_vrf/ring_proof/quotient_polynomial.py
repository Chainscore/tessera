
from sympy import symbols, simplify, expand,mod_inverse
from sympy.matrices.expressions.slice import normalize

from jam.ring_vrf.ring_proof.constants import S_PRIME, omega, S_ORDER
from jam.ring_vrf.ring_proof.polynomial_interpolation import poly_evaluate
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import commit_to_polynomial
from fiat_shamir_funcs import fiat_shamir_evaluation_point
from jam.ring_vrf.ring_proof.prover_witness_polynomials import b_v_I,acc_x_I,acc_y_I,acc_ip_I,b_v,acc_ip,acc_y,acc_x
from jam.ring_vrf.ring_proof.preprocessing import px_I,py_I,s_v_I,px_v,py_v, s_vector
from jam.ring_vrf.ring_proof.constraints_aggregation import cs_aggregation
from jam.ring_vrf.ring_proof.poly_interpolation_fft import poly_interpolate_fft,fft

# from jam.ring_vrf.ring_proof.polynomial_interpolation import interpolated_poly_at_index
# x=symbols('x')

# def quotient_polynomial(c_x):
#     """
#     input: aggregated polynomial
#     output: Quotient polynomial
#     """
#     # contraint_vals=fft(c_x,omega,S_PRIME)
#     # q_coeffs= poly_interpolate_fft(contraint_vals, omega,S_PRIME)
#     # return q_coeffs\


def poly_divide(P_coeff, Q_coeff):
    """
    Perform polynomial division: P(x) / Q(x).
    P_coeff and Q_coeff are coefficient vectors from constant to highest degree.

    Returns:
        quotient_coeff: Coefficients of the quotient polynomial.
        remainder_coeff: Coefficients of the remainder polynomial.
    """
    # Initialize quotient and remainder
    quotient_coeff = [0] * (len(P_coeff) - len(Q_coeff) + 1)
    remainder_coeff = P_coeff[:]

    # Degree of P(x) and Q(x)
    degree_P = len(P_coeff) - 1
    degree_Q = len(Q_coeff) - 1

    # Perform division (similar to long division)
    while degree_P >= degree_Q:
        # Divide leading term of remainder by leading term of Q(x)
        lead_term_quotient = remainder_coeff[degree_P] / Q_coeff[degree_Q]

        # Degree of the current quotient term
        quotient_degree = degree_P - degree_Q

        # Update the quotient coefficients
        quotient_coeff[quotient_degree] = lead_term_quotient

        # Subtract (lead_term_quotient * Q(x)) from the remainder
        for i in range(degree_Q + 1):
            remainder_coeff[degree_P - degree_Q + i] -= lead_term_quotient * Q_coeff[i]

        # Remove leading zeros from the remainder (if any)
        while len(remainder_coeff) > 1 and remainder_coeff[0] == 0:
            remainder_coeff.pop(0)

        # Update degree of remainder
        degree_P = len(remainder_coeff) - 1

    # The remainder is already of a smaller degree than Q(x), so we stop here
    return quotient_coeff, remainder_coeff



def poly_vector_xn_minus_1(n):
    vec = [0] * (n+1)
    vec[0] = -1
    vec[n] = 1
    return vec



def fft_poly_div(c_coeffs, d_coeffs, omega, p):
    deg_c = len(c_coeffs) - 1
    deg_d = len(d_coeffs) - 1
    max_deg_q = deg_c - deg_d

    # Find smallest power of 2 ≥ deg_c + 1
    n = 1 << (deg_c + 1).bit_length()

    # Pad inputs
    c = c_coeffs + [0] * (n - len(c_coeffs))
    d = d_coeffs + [0] * (n - len(d_coeffs))

    # FFT of both polys
    c_eval = fft(c, omega, p)
    d_eval = fft(d, omega, p)

    # Pointwise division
    q_eval = []
    for i in range(n):
        if d_eval[i] == 0:
            q_eval.append(0)  # OR handle div-by-zero differently
        else:
            q_eval.append((c_eval[i] * mod_inverse(d_eval[i], p)) % p)

    # Inverse FFT to get quotient coefficients
    q_coeffs = poly_interpolate_fft(q_eval, omega, p)

    # Trim quotient to expected degree
    return q_coeffs[:max_deg_q + 1]


def poly_division_general(c, d, p=None):
    """
    c: list of coefficients for numerator (highest degree last)
    d: list of coefficients for denominator
    p: optional modulus (for finite field arithmetic)
    returns (quotient, remainder)
    """
    c = c[:]  # copy to avoid modifying input
    deg_c = len(c) - 1
    deg_d = len(d) - 1

    if deg_c < deg_d:
        return ([0], c)

    quotient = [0] * (deg_c - deg_d + 1)

    while len(c) >= len(d):
        coeff = c[-1]
        deg_diff = len(c) - len(d)

        if p:
            inv = mod_inverse(d[-1], p)
            coeff = (coeff * inv) % p
        else:
            coeff = coeff / d[-1]

        quotient[deg_diff] = coeff

        # Subtract (coeff * d * x^deg_diff) from c
        for i in range(len(d)):
            if p:
                c[deg_diff + i] = (c[deg_diff + i] - coeff * d[i]) % p
            else:
                c[deg_diff + i] -= coeff * d[i]

        # Remove trailing zeroes
        while c and c[-1] == 0:
            c.pop()

    return (quotient, c)  # quotient, remainder





def quotient_poly_commitment(q_x):
    """
    input: quotient polynomial
    output: commitment to quotient polynomial
    """
    c_q= commit_to_polynomial(q_x)
    return c_q

def evaluation_point_at(c_q):
    """
    input: quotient commitment
    output : Evaluation Point
    """
    zeta=fiat_shamir_evaluation_point(c_q)
    return zeta


def relevant_poly_evaluation(poly,zeta):
    """
    calculate px,py, accx, accy, accip, s, b poly's at given Zeta
    """
    interpolated_poly= poly_evaluate(poly,zeta,S_PRIME)
    return interpolated_poly


x_n_m_1=poly_vector_xn_minus_1(512) #TO FIND[-1,0'S(511),1]
quotient_poly=fft_poly_div(cs_aggregation, x_n_m_1, omega,S_PRIME)
# quotient_poly=quotient_polynomial(cs_aggregation)
print('agg_len:', len(cs_aggregation))
print("x**N -1:", x_n_m_1, len(x_n_m_1))
print("quotient poly:",quotient_poly,len(quotient_poly))


C_q=quotient_poly_commitment(quotient_poly)

print("Quotient poly commitment:",C_q)



Evaluation_point_Zeta=22347561174510102643490174453933951710403571909463385254138988912759167360136#evaluation_point_at(C_q)###########22347561174510102643490174453933951710403571909463385254138988912759167360136#
print("Zeta",Evaluation_point_Zeta)

print("Quotient poly evaluation initial:", poly_evaluate(quotient_poly, Evaluation_point_Zeta,S_PRIME))

#Relevant polynomials Evaluation
P_x_zeta=relevant_poly_evaluation(px_I,Evaluation_point_Zeta)
P_y_zeta=relevant_poly_evaluation(py_I,Evaluation_point_Zeta)
s_zeta=relevant_poly_evaluation(s_v_I,Evaluation_point_Zeta)
b_zeta=relevant_poly_evaluation(b_v_I,Evaluation_point_Zeta)
acc_ip_zeta=relevant_poly_evaluation(acc_ip_I,Evaluation_point_Zeta)
acc_x_zeta=relevant_poly_evaluation(acc_x_I,Evaluation_point_Zeta)
acc_y_zeta= relevant_poly_evaluation(acc_y_I,Evaluation_point_Zeta)
from py_ecc.optimized_bls12_381 import normalize as n
print("P_x_zeta",P_x_zeta)
print("P_y_zeta", P_y_zeta)
print("s_zeta:", s_zeta)
print("b_zeta:", b_zeta)
print("acip_zeta:",acc_ip_zeta)
print("acc_x_zeta:",acc_x_zeta)
print("acc_y_zeta:", acc_y_zeta)

print("Quotient poly commitment:",C_q)
print("Normalized q poly comitment:", n(C_q))

# print(Evaluation_point_Zeta>S_PRIME) #false
# print(Evaluation_point_Zeta>field_modulus) #false
# print(Evaluation_point_Zeta>S_ORDER) #true


