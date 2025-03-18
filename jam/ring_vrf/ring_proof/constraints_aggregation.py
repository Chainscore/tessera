from sympy import symbols, expand, prod, mod_inverse, pprint
import hashlib
import random
from py_ecc.optimized_bls12_381 import normalize

import sys

from jam.ring_vrf.ring_proof.helpers import do_modulus

# Increase the maximum number of digits allowed
sys.set_int_max_str_digits(1000000)


from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import commit_to_polynomial
from jam.ring_vrf.ring_proof.constants import S_PRIME
from jam.ring_vrf.ring_proof.preprocessing import D
from jam.ring_vrf.ring_proof.prover_witness_polynomials import C_b_v,C_acc_x,C_acc_ip,C_acc_y
from jam.ring_vrf.ring_proof.constraints_polynomials import c1x, c2x, c3x, c4x, c5x, c6x, c7x


def hash_commitments(commitments):
    """
    """
    hasher = hashlib.sha512()

    for commitment in commitments:
        # Convert projective (X, Y, Z) -> affine (x, y)
        x, y = normalize(commitment)  # Normalize converts to affine

        # Convert x, y to bytes and update hash
        hasher.update(x.n.to_bytes(48, 'little'))  # Convert field element to bytes
        hasher.update(y.n.to_bytes(48, "little"))

    return int.from_bytes(hasher.digest(), 'little')


def generate_alpha(commitments, num_alphas=7):
    """
    """
    seed = hash_commitments(commitments)  # Get deterministic seed from commitments
    random.seed(seed)
    # Seed PRNG for deterministic outputs
    return [random.randint(0, 2 ** 256 - 1) for _ in range(num_alphas)]  # Generate alpha values



def construct_aggregation_constraint(alphas, constraints, domain):
    """
    """
    x = 0  # Symbolic variable for polynomial construction

    c_x=0
    # Compute the weighted sum of constraints
    for i in range(len(alphas)):
        c_x+=alphas[i] * constraints[i]
        c_x+=do_modulus(constraints[i])

    # Multiply by (x - ω^(N-3)) (x - ω^(N-2)) (x - ω^(N-1))
    c_x=expand(c_x)
    # print('modulo cx')
   #vanishing term
    # vanishing_term=1
    # for k in range(3):
    #     vanishing_term*= domain[x]-domain[-1-k] #W^N-k (W^N is the last element of D)

    # Final aggregated constraint

    # c_x *= vanishing_term
    # print('to do mod after v t')
    return expand(c_x)% S_PRIME # Expand polynomial for better readability


#Get the apa values from the Prover's commitments
commitments = [C_b_v,C_acc_x,C_acc_y,C_acc_ip]
constraints=[c1x,c2x,c3x,c4x,c5x,c6x,c7x]


alpha_values = generate_alpha(commitments)
alpha_values=[alpha% S_PRIME for alpha in alpha_values]

x,omega_x,N_m4=symbols('x omega_x N_m4')
idx=0
print(alpha_values)
cs_aggregation=construct_aggregation_constraint(alpha_values,constraints,D)

substitutions = {x: D[idx], omega_x: D[idx+1], N_m4: D[-5]}
final_result = cs_aggregation.subs(substitutions)

print("Alpha Values:",alpha_values)
pprint(cs_aggregation, wrap_line=False)
print("Constraint Aggregated:",cs_aggregation)
print("final result:",final_result)


