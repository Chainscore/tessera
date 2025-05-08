
from sympy import symbols, simplify, expand,mod_inverse
from jam.ring_vrf.ring_proof.constants import S_PRIME
from jam.ring_vrf.ring_proof.fiat_shamir_with_transcript import zeta
from jam.ring_vrf.ring_proof.poly_interpolation_fft import poly_interpolate_fft
from jam.ring_vrf.ring_proof.polynomial_vect_ops import poly_evaluate
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import commit_to_polynomial
from jam.ring_vrf.ring_proof.prover_witness_polynomials import b_v_I,acc_x_I,acc_y_I,acc_ip_I
from jam.ring_vrf.ring_proof.preprocessing import px_I,py_I,s_v_I
from jam.ring_vrf.ring_proof.constraints_aggregation import final_agg_cst
from py_ecc.optimized_bls12_381 import normalize


def poly_vector_xn_minus_1(n):
    vec = [0] * (n+1)
    vec[0] = -1
    vec[n] = 1
    return vec


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
    return quotient, c  # quotient, remainder



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
    z=zeta
    return z


def relevant_poly_evaluation(poly,zeta):
    """
    calculate px,py, accx, accy, accip, s, b poly's at given Zeta
    """
    interpolated_poly= poly_evaluate(poly,zeta,S_PRIME)
    return interpolated_poly


x_n_m_1=poly_vector_xn_minus_1(512) #TO FIND[-1,0'S(511),1]
quotient_poly=poly_division_general(final_agg_cst, x_n_m_1, S_PRIME)[0]
print('agg_len:', len(final_agg_cst))
print("x**N -1:", x_n_m_1, len(x_n_m_1))
print("quotient poly:",quotient_poly,len(quotient_poly))
C_q=quotient_poly_commitment(quotient_poly)
print("Quotient poly commitment:",C_q)

Evaluation_point_Zeta= evaluation_point_at(C_q)[0]
print("Zeta",Evaluation_point_Zeta)

#Relevant polynomials Evaluation
P_x_zeta=relevant_poly_evaluation(px_I,Evaluation_point_Zeta)
P_y_zeta=relevant_poly_evaluation(py_I,Evaluation_point_Zeta)
s_zeta=relevant_poly_evaluation(s_v_I,Evaluation_point_Zeta)
b_zeta=relevant_poly_evaluation(b_v_I,Evaluation_point_Zeta)
acc_ip_zeta=relevant_poly_evaluation(acc_ip_I,Evaluation_point_Zeta)
acc_x_zeta=relevant_poly_evaluation(acc_x_I,Evaluation_point_Zeta)
acc_y_zeta= relevant_poly_evaluation(acc_y_I,Evaluation_point_Zeta)

print("P_x_zeta",P_x_zeta)
print("P_y_zeta", P_y_zeta)
print("s_zeta:", s_zeta)
print("b_zeta:", b_zeta)
print("acip_zeta:",acc_ip_zeta)
print("acc_x_zeta:",acc_x_zeta)
print("acc_y_zeta:", acc_y_zeta)
print("Quotient poly commitment:",C_q)
print("Normalized q poly comitment:", normalize(C_q))