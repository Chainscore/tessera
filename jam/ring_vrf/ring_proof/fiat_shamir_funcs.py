import hashlib
import random
from jam.ring_vrf.ring_proof.constants import S_PRIME


#Fiat-Shamir for Evaluation Challenge
def fiat_shamir_evaluation_challenge(commitment):
    """Generate Fiat-Shamir-based evaluation challenge ζ."""
    data = commitment.encode()
    hashed_value = hashlib.sha256(data).hexdigest()

    # Convert hash into a large integer and map to field range
    zeta = int(hashed_value, 16) % S_PRIME  # Modulo a large prime field in real applications
    return zeta



#Fiat shamir for final proof aggregation coefficients
def fiat_shamir_final_aggregation(values, num_coeffs=8):
    """Generate Fiat-Shamir-based aggregation coefficients ν_i."""
    # Convert all values to a single string
    data = "".join(map(str, values)).encode()
    # Compute the hash
    hashed_value = hashlib.sha256(data).hexdigest()
    # Convert hash to random coefficients
    random.seed(int(hashed_value, 16))
    return [random.randint(1, 10 ** 6) for _ in range(num_coeffs)]  # Simulated random coefficients



