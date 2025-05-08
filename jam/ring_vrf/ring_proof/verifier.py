import time
from jam.ring_vrf.ring_proof.constants import S_PRIME, SIZE, D, omega,SeedPoint
start_is=time.time()
from jam.ring_vrf.ring_proof.fiat_shamir_with_transcript import alphas, zeta, cf_vectors
from jam.ring_vrf.ring_proof.polynomial_vect_ops import lagrange_basis_polynomial, poly_evaluate
from jam.ring_vrf.ring_proof.preprocessing import C_px, C_py, C_s, Result_plus_Seed
from jam.ring_vrf.ring_proof.prover_witness_polynomials import Result_point
from jam.ring_vrf.ring_proof.short_weierstrass import twisted_edward_to_sw
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import verify_kzg_proof
from sympy import mod_inverse
from py_ecc.optimized_bls12_381 import multiply, add, Z1, curve_order
from jam.ring_vrf.ring_proof.aggregation_poly_proof_construction import prover_proof as verifier_proof


E_zeta=zeta[0]

def recover_fiat_shamir_challeneges(Proof_Phi):
    """
    input:Proof
    output: FS Challenges
    """
    Cb, Cip, Caccx, Caccy, px_zeta,py_zeta, s_zeta, b_zeta, accip_zeta, accx_zeta, accy_zeta,Cq, l_zeta_omega,Phi_zeta, Phi_zeta_omega=Proof_Phi
    alpha_list=alphas #generate_alpha([Cb, Cip, Caccx,Caccy])
    zeta_p= zeta[0]#fiat_shamir_evaluation_point(Cq)
    V_list= cf_vectors#fiat_shamir_final_aggregation([px_zeta,py_zeta,s_zeta,b_zeta,accip_zeta, accx_zeta, accy_zeta, l_zeta_omega])
    return alpha_list, zeta_p, V_list


def contributions_to_constraints_eval_at_zeta(Proof_Phi, zeta, result, sp, D):
    Cb, Cip, Caccx, Caccy, px_zeta, py_zeta, s_zeta, b_zeta, accip_zeta, accx_zeta, accy_zeta, Cq, l_zeta_omega, Phi_zeta, Phi_zeta_omega = verifier_proof
    L_0_x = lagrange_basis_polynomial(D, 0)
    L_0_zeta= poly_evaluate(L_0_x, zeta, S_PRIME) % curve_order
    L_N_4_x = lagrange_basis_polynomial(D, SIZE - 4)
    L_N_4_zeta=poly_evaluate(L_N_4_x, zeta, S_PRIME) % curve_order
    sp=twisted_edward_to_sw(sp)
    sx,sy=sp
    rx,ry=result

    MOD = curve_order

    # Constraint 1

    term1 = (b_zeta * s_zeta) % MOD
    inner_sum = (accip_zeta + term1) % MOD
    negated = (-inner_sum) % MOD  # Ensures result is positive in the field
    vanishing_term = (zeta - D[-4]) % MOD
    c1_zeta = (negated * vanishing_term) % MOD

    # Constraint 2
    term1 = ((accx_zeta - px_zeta) ** 2) % MOD
    term1 = (term1 * ((accx_zeta + px_zeta) % MOD)) % MOD
    term2 = ((py_zeta - accy_zeta) ** 2) % MOD
    c2_inner = (term1 - term2) % MOD
    c2 = (b_zeta * c2_inner) % MOD
    c2 = (c2 - ((1 - b_zeta) * accy_zeta) % MOD) % MOD
    c2_zeta = (c2 * ((zeta - D[-4]) % MOD)) % MOD

    # Constraint 3
    term1 = ((accx_zeta - px_zeta) * accy_zeta) % MOD
    term2 = ((py_zeta - accy_zeta) * accx_zeta) % MOD
    c3 = (b_zeta * ((term1 + term2) % MOD)) % MOD
    c3 = (c3 - ((1 - b_zeta) * accx_zeta) % MOD) % MOD
    c3_zeta = (c3 * ((zeta - D[-4]) % MOD)) % MOD

    # Constraint 4
    c4_zeta = (b_zeta * (1 - b_zeta)) % MOD

    # Constraint 5
    term1 = ((accx_zeta - sx) * L_0_zeta) % MOD
    term2 = ((accx_zeta - Result_plus_Seed[0]) * L_N_4_zeta) % MOD
    c5_zeta = (term1 + term2) % MOD

    # Constraint 6
    term1 = ((accy_zeta - sy) * L_0_zeta) % MOD
    term2 = ((accy_zeta - Result_plus_Seed[1]) * L_N_4_zeta) % MOD
    c6_zeta = (term1 + term2) % MOD

    # Constraint 7
    term1 = (accip_zeta * L_0_zeta) % MOD
    term2 = ((accip_zeta - 1) * L_N_4_zeta) % MOD
    c7_zeta = (term1 + term2) % MOD

    # c1_zeta = -(acc_ip_zeta + (b_zeta * s_zeta)) * (zeta - (omega_N - 4))

    # c1_zeta= ((-(accip_zeta + (b_zeta*s_zeta)%curve_order) % curve_order)* (zeta - D[-4]) % curve_order)%curve_order
    #
    #
    # c2_zeta= ((b_zeta*((accx_zeta- px_zeta )**2 *(accx_zeta+px_zeta)-((py_zeta- accy_zeta)**2))- ((1- b_zeta) * accy_zeta))*
    #           (zeta - D[-4]))
    #
    # c3_zeta=(b_zeta*((accx_zeta- px_zeta)*accy_zeta + (py_zeta- accy_zeta)*accx_zeta) -((1- b_zeta)*accx_zeta)) *(zeta- D[-4])
    #
    # c4_zeta=b_zeta*(1- b_zeta)
    #
    #
    # c5_zeta= (accx_zeta- sx) *L_0_zeta + ( accx_zeta - Result_plus_Seed[0])*L_N_4_zeta
    #
    # c6_zeta= (accy_zeta - sy) * L_0_zeta + ( accy_zeta - Result_plus_Seed[1]) * L_N_4_zeta
    #
    # c7_zeta= accip_zeta* L_0_zeta +  (accip_zeta -1) *L_N_4_zeta

    return c1_zeta, c2_zeta, c3_zeta, c4_zeta, c5_zeta, c6_zeta, c7_zeta


def divide(numr,denom):
    # Compute inverse
    denominator_inv = mod_inverse(denom, curve_order) #which prime modulus need o be taken!

    # Compute final result
    q_zeta = numr* denominator_inv % curve_order#field_modulus

    return q_zeta



def evaluation_of_quotient_poly_at_zeta(Proof_Phi,  pp_commitments, zeta, result, sp, D):
    """
    input: commitments, alphas, zeta,
    output:
    """
    Cb, Caccip, Caccx, Caccy, px_zeta, py_zeta, s_zeta, b_zeta, accip_zeta, accx_zeta, accy_zeta, Cq, l_zeta_omega, Phi_zeta, Phi_zeta_omega = verifier_proof
    alphas_list, zeta, v_list =  recover_fiat_shamir_challeneges(Proof_Phi)

    print("alphas_list:",alphas_list)
    print("zeta",zeta)
    print("v_list",v_list)
    cs=contributions_to_constraints_eval_at_zeta(Proof_Phi,zeta, result, sp,D)
    Cpx, Cpy, Cs= pp_commitments
    C_a=[Cpx,Cpy,Cs, Cb, Caccip, Caccx, Caccy, Cq] #commitments which are in bls12 field form
    prod_sum=1
    for k in range(1,4):
        cur=zeta - D[-k] % curve_order
        prod_sum*=cur % curve_order

    s_sum=0
    for i in range(len(alphas_list)):
        s_sum+= (alphas_list[i]* cs[i] %curve_order ) % curve_order

    s_sum+= l_zeta_omega % curve_order

    q_zeta= divide((s_sum * prod_sum) % curve_order, (pow(zeta, SIZE, curve_order) -1)%curve_order) #poly divide
    print("q_zeta at verifier end:", q_zeta)
    # C_agg= v_list[0]* Cpx + v_list[1]* Cpy + v_list[2]* Cs + v_list[3]*Cb + v_list[4]*Caccip + v_list[5]* Caccx + v_list[6] * Caccy + v_list[7]* Cq

    C_agg=Z1
    for i in range(len(C_a)):
        C_agg=add(C_agg, multiply(C_a[i],v_list[i]))

    MOD= curve_order

    terms = [
        (v_list[0] * px_zeta) % MOD,
        (v_list[1] * py_zeta) % MOD,
        (v_list[2] * s_zeta) % MOD,
        (v_list[3] * b_zeta) % MOD,
        (v_list[4] * accip_zeta) % MOD,
        (v_list[5] * accx_zeta) % MOD,
        (v_list[6] * accy_zeta) % MOD,
        (v_list[7] * q_zeta) % MOD
    ]

    #1
    Agg_zeta =sum(terms) % MOD

    print("Agg at Zeta inside verify:", Agg_zeta)
    #this will change if we ought to take Cs as a point
    # Agg_zeta = v_list[0] * px_zeta + v_list[1] * py_zeta + v_list[2] * s_zeta + v_list[3] * b_zeta + v_list[4] * accip_zeta+ v_list[
    #     5] * accx_zeta + v_list[6] * accy_zeta + v_list[7] * q_zeta

    verification= verify_kzg_proof(C_agg, Phi_zeta, zeta, Agg_zeta)

    # print("are they same:",Agg_zeta==poly_evaluate(agg_poly,zeta,S_PRIME))
    return verification, cs


def evaluation_of_linearization_poly_at_zeta_omega(Proof_Phi,zeta):
    Cb, Caccip, Caccx, Caccy, px_zeta, py_zeta, s_zeta, b_zeta, accip_zeta, accx_zeta, accy_zeta, Cq, l_zeta_omega, Phi_zeta, Phi_zeta_omega = Proof_Phi
    #CL1,2,3, generation depends on the Commitment types(scalar/points)

    # Cl1=(zeta - D[-4])*Caccip
    Cl1=multiply(Caccip, (zeta-D[-4])%curve_order)

    # Cl2=(zeta- D[-4])*((b_zeta*(accx_zeta- px_zeta)**2)*Caccx + (1-b_zeta)*Caccy)
    # Cl2=multiply(add(multiply(Caccx,(b_zeta*(accx_zeta- px_zeta)**2)) , multiply(Caccy,(1-b_zeta))),zeta-D[-4])
    Cl2 = multiply(
        add(
            multiply(Caccx, (b_zeta * pow(accx_zeta - px_zeta,2,curve_order)) % curve_order),
            multiply(Caccy, (1 - b_zeta) % curve_order)
        ),
        (zeta - D[-4]) % curve_order
    )

    # Cl3=(zeta- D[-4])*(((b_zeta*( accy_zeta- py_zeta)+ (1- b_zeta))*Caccx)+ b_zeta*(accx_zeta- px_zeta)*Caccy)
    # Cl3=multiply(add(multiply(Caccx,(b_zeta*( accy_zeta- py_zeta)+ (1- b_zeta))), multiply(Caccy,b_zeta*(accx_zeta- px_zeta))), zeta- D[-4])

    Cl3 = multiply(
        add(
            multiply(
                Caccx,
                (b_zeta * (accy_zeta - py_zeta) + (1 - b_zeta)) % curve_order
            ),
            multiply(
                Caccy,
                (b_zeta * (accx_zeta - px_zeta)) % curve_order
            )
        ),
        (zeta - D[-4]) % curve_order
    )

    Cl_list=[Cl1,Cl2,Cl3]
    alphas_list, zeta, v_list =recover_fiat_shamir_challeneges(Proof_Phi)
    print("alphas_list:", alphas_list)
    print("zeta", zeta)
    print("v_list", v_list)

    Cl=Z1
    for i in range(3):
        Cl=add(Cl, multiply(Cl_list[i],alphas_list[i]))

    print("Verfier End Commitment:", Cl)
    print("L_Zeta_Omega_In_Verify:",l_zeta_omega)

    verified=verify_kzg_proof(Cl,  Phi_zeta_omega, zeta*omega%curve_order, l_zeta_omega)
    return verified


pp_commitments=[C_px,C_py, C_s ]

proof_1, cs= evaluation_of_quotient_poly_at_zeta(verifier_proof, pp_commitments, E_zeta, Result_point,SeedPoint,D)
proof_2=evaluation_of_linearization_poly_at_zeta_omega(verifier_proof,E_zeta)
end_is=time.time()
print("proof 1 is valid:",proof_1)
print("proof 2 is valid:", proof_2)
print("evaluation_point_zeta:",E_zeta)
print("Overall time is:",end_is-start_is)
print("constriants_at_zeta", cs)
