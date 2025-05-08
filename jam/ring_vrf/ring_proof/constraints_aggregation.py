import hashlib
import random
import sys
from jam.ring_vrf.ring_proof.fiat_shamir_with_transcript import alphas
from jam.ring_vrf.ring_proof.poly_interpolation_fft import poly_interpolate_fft
from jam.ring_vrf.ring_proof.polynomial_vect_ops import vect_add, vect_scalar_mul, poly_multiply
from jam.ring_vrf.ring_proof.constants import S_PRIME, D, omega, omega_2048
from jam.ring_vrf.ring_proof.prover_witness_polynomials import C_b_v,C_acc_x,C_acc_ip,C_acc_y
from jam.ring_vrf.ring_proof.constraints_polynomial_evals import c1x, c2x, c3x, c4x, c5x, c6x, c7x

sys.set_int_max_str_digits(1000000)

constraints=[c1x,c2x,c3x,c4x,c5x,c6x,c7x]
commitments = [C_b_v,C_acc_x,C_acc_y,C_acc_ip]


def aggregate_evaluations(polys, coeffs, mod=None):
    """Aggregate evaluation vectors using scalar coefficients."""
    assert len(polys) == len(coeffs)
    result = [0] * len(polys[0])
    for poly, coeff in zip(polys, coeffs):
        weighted = vect_scalar_mul(poly, coeff, mod)
        result = vect_add(result, weighted, mod)
    return result


def generate_alphas(commits, n=7):

    alpha_list=alphas
    return alpha_list



def remove_trailing_zeros(arr):
    i = len(arr) - 1
    while i >= 0 and arr[i] == 0:
        i -= 1
    return arr[:i+1]


def mul_with_vanishing_poly(aggregated_constraint, prime):
    vanishing_term = [1]
    for k in range(1, 4):
        vanishing_term = poly_multiply(vanishing_term, [-D[-k], 1],
                                       prime)  # x-W^N-k (W^N-1 is the last element of D)

    # vanishing_poly = [27611812781829920551290133267575249478648871281233506899293410857719571783635,
    #                   18588772761366545515353714920513821262872352644173316860176739225353543051128,
    #                   21856349314143507620628005048545870461349664960990502850349462173747080309275,
    #                   1]

    print("Vansh:", vanishing_term)

    final_cs_agg= poly_multiply(aggregated_constraint, vanishing_term,prime)

    return final_cs_agg


#Get the alpha values from the Prover's commitments
alpha_values = generate_alphas(commitments, 7)
cs_aggregation=aggregate_evaluations(constraints,alpha_values,S_PRIME)

print("Constraint Aggregated:", cs_aggregation,len(cs_aggregation))

Interpolated_poly=poly_interpolate_fft(cs_aggregation, omega_2048,S_PRIME)

print("Interpolated_poly:",Interpolated_poly)

Interpolated_poly=remove_trailing_zeros(Interpolated_poly)

print("Interpolated_poly:",Interpolated_poly)
print("Alpha Values:",alpha_values)

# print("AGGE RESULT:",cs_aggregation)

#Expected
# Vector:["", "5291858017394326220327389462579461719080734283449386752065209561883729801330",
#           "33555693263795842704974598853766205191665487365954216337482772216222023911745",
#           "8411120379136671107946066988856908149731468707639881684643532326074864901112",
#           "", "19877707608549581885228899168610643567678711376936252844274555508244350760960",

final_agg_cst=mul_with_vanishing_poly(Interpolated_poly, S_PRIME)

print("Final Agg:", final_agg_cst)


