from sympy import symbols, Poly
from jam.ring_vrf.ring_proof.constants import omega, S_PRIME, D
from jam.ring_vrf.ring_proof.prover_witness_polynomials import acc_x_I, acc_y_I, acc_ip_I
from jam.ring_vrf.ring_proof. polynomial_interpolation import poly_add,poly_subtract,poly_multiply,poly_scalar,poly_evaluate
from jam.ring_vrf.ring_proof.quotient_polynomial import P_x_zeta, P_y_zeta, acc_x_zeta, acc_y_zeta, acc_ip_zeta, s_zeta, \
    b_zeta, Evaluation_point_Zeta
from jam.ring_vrf.ring_proof.constraints_aggregation import alpha_values
import sys
sys.set_int_max_str_digits(10000)

scalar_term = (Evaluation_point_Zeta - D[-4] % S_PRIME)

# l1 = (zeta - omega^(N - 4)) * acc_ip_I
l1 = poly_scalar(acc_ip_I, scalar_term,S_PRIME)

# l2 = (zeta - omega^(N - 4)) * (b_zeta * (acc_x_zeta - px_zeta)**2) *( acc_x_I) + (1 - b_zeta) * acc_y_I)

l2=poly_scalar(poly_add(poly_scalar(acc_x_I,b_zeta*pow(acc_x_zeta-P_x_zeta,2,S_PRIME)%S_PRIME, S_PRIME) , poly_scalar(acc_y_I, (1- b_zeta),S_PRIME),S_PRIME), scalar_term, S_PRIME)


l3= poly_scalar(poly_add(poly_scalar(acc_x_I,(b_zeta*((acc_y_zeta-P_y_zeta)%S_PRIME)%S_PRIME + (1- b_zeta)%S_PRIME), S_PRIME),
                         poly_scalar(acc_y_I,b_zeta*((acc_x_zeta - P_x_zeta)%S_PRIME) %S_PRIME ,S_PRIME),S_PRIME),
                scalar_term, S_PRIME
                )

zeta_omega=(Evaluation_point_Zeta * omega ) % S_PRIME


def linearization_contraint_aggregated(l1,l2,l3,alphas):
    l_c=[l1,l2,l3]
    l_x=[0]
    for i in range(len(l_c)):
        l_x= poly_add(l_x,poly_scalar(l_c[i],alphas[i],S_PRIME),S_PRIME)
    return l_x

import time
st_time=time.time()
l_agg=linearization_contraint_aggregated(l1,l2,l3,alpha_values)

l_agg_at_zeta_omega = poly_evaluate(l_agg, zeta_omega, S_PRIME)

end_time=time.time()

print("l_agg:",l_agg)
print("value of l_agg_zeta_omega:",l_agg_at_zeta_omega)
# print('tt;',end_time-st_time)
print("zeta_omega:",zeta_omega)

