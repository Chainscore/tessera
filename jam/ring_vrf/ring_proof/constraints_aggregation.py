
import hashlib
import random
from py_ecc.optimized_bls12_381 import normalize
import sys
from jam.ring_vrf.ring_proof.polynomial_interpolation import poly_scalar, poly_multiply, poly_add
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import commit_to_polynomial
from jam.ring_vrf.ring_proof.constants import S_PRIME,D
from jam.ring_vrf.ring_proof.preprocessing import end_time
from jam.ring_vrf.ring_proof.prover_witness_polynomials import C_b_v,C_acc_x,C_acc_ip,C_acc_y
from jam.ring_vrf.ring_proof.constraints_polynomials import c1x, c2x, c3x, c4x, c5x, c6x, c7x


sys.set_int_max_str_digits(1000000)

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
    return [random.randint(1, S_PRIME) for _ in range(num_alphas)]  # Generate alpha values



def construct_aggregation_constraint(alphas, constraints, domain):
    """
    """
    # x = 1
    c_x=[0]
    # Compute the weighted sum of constraints
    for i in range(len(alphas)):

        c_x=poly_add(poly_scalar(constraints[i],alphas[i],S_PRIME),c_x,S_PRIME)

    # Multiply by (x - ω^(N-3)) (x - ω^(N-2)) (x - ω^(N-1))
    # print('modulo cx')
   #vanishing term
    vanishing_term=[1]
    for k in range(3):
        vanishing_term= poly_multiply(vanishing_term,[-domain[0-k],1],S_PRIME)#x-W^N-k (W^N-1 is the last element of D)

    # Final aggregated constraint
    c_x = poly_multiply(c_x,vanishing_term,S_PRIME)
    # print('to do mod after v t')
    return c_x

#Get the apa values from the Prover's commitments
commitments = [C_b_v,C_acc_x,C_acc_y,C_acc_ip]
constraints=[c1x,c2x,c3x,c4x,c5x,c6x,c7x]

# alpha_values = generate_alpha(commitments)
# alpha_values=[alpha% S_PRIME for alpha in alpha_values]
alpha_values=[23426295910140870709614097412433960347746242342772840884066757906985100343590, 46433544455077235545632682909406958794646428824021350807274305193686650751236, 78101732610314093593150729898315267434854171850795179589607409285815531790, 593197255987830876876009860956149019051956889376694517098490195230307214182, 32175196951432882449291708537928919219460156628583290699727577517487325664113, 34948741935357743784650851171470586551760506493489743006361967647813201562252, 48766446903835583133423634840534770408834461876682423474505157724475361584745]
print(alpha_values)
cs_aggregation=construct_aggregation_constraint(alpha_values,constraints,D)

# substitutions = {x: D[idx], omega_x: D[idx+1], N_m4: D[-5]}
# final_result = cs_aggregation.subs(substitutions)

print("Alpha Values:",alpha_values)
print("Constraint Aggregated:", cs_aggregation,len(cs_aggregation))
# print("final result:",final_result)


