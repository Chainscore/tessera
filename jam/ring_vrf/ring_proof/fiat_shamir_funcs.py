import hashlib
import random
from jam.ring_vrf.ring_proof.constants import S_PRIME
from py_ecc.optimized_bls12_381 import normalize, field_modulus

#Fiat-Shamir for Evaluation Challenge
def fiat_shamir_evaluation_point(commitment):
    """Generate Fiat-Shamir-based evaluation challenge ζ."""
    hasher = hashlib.sha512()
    # Convert projective (X, Y, Z) -> affine (x, y)
    x, y = normalize(commitment)  # Normalize converts to affine
    # Convert x, y to bytes and update hash
    hasher.update(x.n.to_bytes(48, 'little'))  # Convert field element to bytes
    hasher.update(y.n.to_bytes(48, "little")) #OR DO WE NEED TO CONVERT THESE BACK TO SHOERT WEIERTRASS? + DO WE NEED TO USE THE POINT_2_Str CONVERSION HERE!!!

    seed = int.from_bytes(hasher.digest(), 'little')
    random.seed(seed)
    # Seed PRNG for deterministic outputs
    return random.randint(0, S_PRIME) #if we take field_modulus it would of bit length 381 i guess


#Fiat shamir for final proof aggregation coefficients
def fiat_shamir_final_aggregation(values, num_coeffs=8):
    """Generate Fiat-Shamir-based aggregation coefficients ν_i."""
    # Convert all values to a single string
    data = "".join(map(str, values)).encode()
    # Compute the hash
    hashed_value = hashlib.sha512(data).hexdigest()
    # Convert hash to random coefficients
    random.seed(int(hashed_value, 16))
    return [random.randint(1,  S_PRIME) for _ in range(num_coeffs)]  # Simulated random coefficients


