from sympy import symbols, simplify, expand

from jam.ring_vrf.ring_proof.constants import S_PRIME
from jam.ring_vrf.ring_proof.preprocessing import size, D
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import commit_to_polynomial
from fiat_shamir_funcs import fiat_shamir_evaluation_challenge
from jam.ring_vrf.ring_proof.prover_witness_polynomials import b_v_I,acc_x_I,acc_y_I,acc_ip_I,b_v,acc_ip,acc_y,acc_x
from jam.ring_vrf.ring_proof.preprocessing import px_I,py_I,s_v_I,px_v,py_v, s_vector
from jam.ring_vrf.ring_proof.constraints_aggregation import cs_aggregation
from jam.ring_vrf.ring_proof.polynomial_interpolation import interpolated_poly_at_index

x=symbols('x')

def quotient_polynomial(c_x):
    """
    input: aggregated polynomial
    output: Quotient polynomial
    """
    N=size
    q_x= c_x/((x**N) -1)

    return simplify(q_x)


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
    zeta=fiat_shamir_evaluation_challenge(c_q)
    return zeta


def relevant_poly_evaluation(Zeta,poly,poly_vector):
    """
    calculate px,py, accx, accy, accip, s, b poly's at given Zeta
    """
    interpolated_poly= interpolated_poly_at_index(Zeta,poly,D,poly_vector)
    return interpolated_poly



quotient_poly=quotient_polynomial(cs_aggregation)
print(quotient_poly)

C_q=quotient_poly_commitment(quotient_poly)
Evaluation_point_Zeta=evaluation_point_at(C_q)

#Relevant polynomials
P_x_zeta=relevant_poly_evaluation(Evaluation_point_Zeta,px_I,px_v)


