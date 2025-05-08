import time
from jam.ring_vrf.ring_proof.fiat_shamir_with_transcript import cf_vectors
start_is=time.time()
from py_ecc.optimized_bls12_381 import normalize
from jam.ring_vrf.ring_proof.constants import S_PRIME
from jam.ring_vrf.ring_proof.polynomial_vect_ops import poly_add, poly_scalar, poly_evaluate
from jam.ring_vrf.ring_proof.quotient_polynomial import P_x_zeta, P_y_zeta, acc_x_zeta, acc_ip_zeta, acc_y_zeta, b_zeta, \
    s_zeta, C_q, quotient_poly, Evaluation_point_Zeta#, Evaluation_point_Zeta
from jam.ring_vrf.ring_proof.linearization_polynomial import l_agg_at_zeta_omega, l_agg, zeta_omega
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import create_kzg_proof as kzg_open, commit_to_polynomial
from jam.ring_vrf.ring_proof.preprocessing import px_I,py_I,s_v_I
from jam.ring_vrf.ring_proof.prover_witness_polynomials import acc_x_I,acc_y_I, acc_ip_I, b_v_I
from jam.ring_vrf.ring_proof.prover_witness_polynomials import C_b_v, C_acc_y, C_acc_x, C_acc_ip


#get the v list
def coeff_list(px_zeta, py_zeta, s_zeta, b_zeta, accip_zeta, accx_zeta, accy_zeta, l_zeta_omega, prime=None):
    """
    input: poly_evaluations
    output: V list
    """
    if not prime:
        prime=S_PRIME

    values=[px_zeta, py_zeta, s_zeta, b_zeta, accip_zeta, accx_zeta, accy_zeta, l_zeta_omega]

    V_list=cf_vectors
    return V_list

# get the aggregated poly
def aggregated_poly(px_x, py_x, s_x, b_x, accip_x, accx_x, accy_x, q_x, v_list):

    poly_I=[px_x,py_x, s_x, b_x , accip_x, accx_x, accy_x, q_x]
    V_list=v_list
    agg_poly=[0]
    for i in range(len(poly_I)):
        agg_poly=poly_add(agg_poly, poly_scalar(poly_I[i], V_list[i], S_PRIME), S_PRIME)

    return agg_poly



def proof_contents_phi(agg, l, zeta, zeta_omega):
    """
    input:agg_poly, liner_poly, zeta, zeta_omega
    output: Phi_zeta, phi_zeta_omega
    """
    phi_zeta, one=kzg_open(agg,zeta) # take only proof
    print("Agg at zeta in proover side:", one)
    phi_zeta_omega, two=kzg_open(l,zeta_omega) #take only proof
    print("L_Zeta_omega in proover side:", two)
    return phi_zeta, phi_zeta_omega

def construct_proof(C_b,C_acc_ip,C_acc_x,C_acc_y,P_x_zeta, P_y_zeta,S_zeta,b_zeta,acc_ip_zeta, acc_x_zeta, acc_y_zeta,C_q,l_zeta_omgea,phi_zeta,phi_zeta_omega):
    """
    input: commitments, poly_evaluations
    output: proof
    """
    Proof_phi=(C_b, C_acc_ip, C_acc_x, C_acc_y, P_x_zeta, P_y_zeta, S_zeta, b_zeta, acc_ip_zeta, acc_x_zeta, acc_y_zeta, C_q,l_zeta_omgea, phi_zeta, phi_zeta_omega)
    return Proof_phi



V_LIST=coeff_list(P_x_zeta,P_y_zeta,s_zeta,b_zeta,acc_ip_zeta, acc_x_zeta,acc_y_zeta,l_agg_at_zeta_omega,S_PRIME)
# print("V_LIST", V_LIST)
agg_poly=aggregated_poly(px_I,py_I, s_v_I, b_v_I, acc_ip_I, acc_x_I, acc_y_I,quotient_poly,V_LIST)


# print("AGG Poly:",agg_poly)
# print("Agg at zeta:", poly_evaluate(agg_poly, Evaluation_point_zeta, S_PRIME))

phi_z, phi_zw=proof_contents_phi(agg_poly,l_agg,Evaluation_point_Zeta, zeta_omega)

prover_proof=construct_proof(C_b_v,C_acc_ip,C_acc_x,C_acc_y,P_x_zeta,P_y_zeta,s_zeta,b_zeta,acc_ip_zeta,acc_x_zeta, acc_y_zeta,C_q, l_agg_at_zeta_omega, phi_z,phi_zw)

end_is=time.time()
print("veriferEnd_proof:",prover_proof)
print("proof generation time:", end_is- start_is)

print(normalize(phi_z))
print(normalize(phi_zw))


