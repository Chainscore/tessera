import Relevant_polynomial_Evoluation
import Fiat_shamir
from sympy import symbols, simplify, prod, EvaluationFailed
import random
import Quotient_Polyomial_implementation
import sys

sys.set_int_max_str_digits(1000000)
import Linearization_polynomial
import R_expected_result_delta

# Size of the domain
N = 8

# Prime field (BLS12-381 curve prime)
p = 0x1A0111EA397FE69A4B1BA7B6434BACD764774B84F38512BF6730D2A0F6B0F6241EABFFFEB153FFFFB9FEFFFFFFFFAAAB

# Seeding Point (Elliptic curve generator point)
Seed_point = (
    3955725774225903122339172568337849452553276548604445833196164961773358506589,
    29870564530691725960104983716673293929719207405660860235233811770612192692323,
)

# Padding Point
Padding_Point = (
    23942223917106120326220291257397678561637131227432899006603244452561725937075,
    1605027200774560580022502723165578671697794116420567297367317898913080293877,
)

# Omega Value which acts as a cyclic Generator of Domain "D"
omega = 49307615728544765012166121802278658070711169839041683575071795236746050763237

# Precompute domain elements D
D = [pow(omega, i, p) for i in range(N)]

# Given list of public keys (short Weierstrass form)
public_keys = [
    (
        208113007836107444597505874445004242520748793534672602173391770229382496673285394326952021584508022728566807227051,
        1533088682837102619025821216617130832820444288537158495221066192636222510878256375098682461212298736484483881126864,
    ),
    (
        2348297384015157327855990817202114003281872780071082543556475427241132151276139270874030784646348975482189176851692,
        692816957730143075491375686558416835292659446454963826152306305382139813920079410737792540136485478908027393831861,
    ),
    (
        316461271518729218525582182311685757964878217669860166326191270922461054750147565085214096770742446503571313055992,
        1942924613523112662086900114445135441167429699354854636321031425277664193413095277535143227320109926501065490383519,
    ),
]


def generate_bits_vector(prover_index, ring_size, t):
    if prover_index >= ring_size:
        raise ValueError("Prover index is out of bounds for the given ring size.")

    # Step 1: Create binary vector k (one-hot encoded for prover index)
    k_vector = [1 if i == prover_index else 0 for i in range(ring_size)]

    # Step 2: Convert secret scalar t to binary representation
    t_binary = [int(bit) for bit in bin(t)[2:].zfill(32)]  # Assuming t is 32-bit

    # Step 3: Append a single 0 for padding
    bits_vector = k_vector + t_binary + [0]

    return bits_vector


def inner_product_accumulator(bits_vector, selector_vector):
    accip = [0]  # Initialize accumulator

    for i in range(len(selector_vector)):  # Iterate up to the ring size
        accip.append((accip[-1] + bits_vector[i] * selector_vector[i]) % p)

    return accip


def conditional_sum_accumulator(bits_vector, public_keys):
    acc = [Seed_point]  # Start with the seeding point
    for i, b in enumerate(bits_vector[: len(public_keys)]):
        Px, Py = public_keys[i]
        acc.append(((acc[-1][0] + b * Px) % p, (acc[-1][1] + b * Py) % p))
    return acc


def interpolate(values, domain):
    x = symbols("x")
    N = len(domain)

    # Pad values with random elements to match the domain size
    padded_values = values + [random.randint(1, 100) for _ in range(N - len(values))]

    # Interpolate using Lagrange polynomials
    polynomial = sum(
        padded_values[i]
        * prod((x - domain[j]) / (domain[i] - domain[j]) for j in range(N) if j != i)
        for i in range(N)
    )
    return simplify(polynomial)


# Polynomial Commitment using PCS (KZG-style)
def pcs_commit(polynomial, srs):
    commitment = sum(
        coef * srs[i]
        for i, coef in enumerate(polynomial.as_coefficients_dict().values())
    )
    return commitment % p


# constraints


def inner_product_constraint(accip_poly, b_poly, s_poly, omega, N):
    x = symbols("x")  # Symbol for the polynomial variable

    # Shifted ACC_{IP} polynomial by domain generator omega
    accip_omega_poly = accip_poly.subs(x, omega * x % p)

    # Inner product constraint
    c1 = simplify(
        (accip_omega_poly - accip_poly - b_poly * s_poly) * (x - omega ** (N - 4))
    )
    return c1


def conditional_addition_constraints(
    accx_poly, accy_poly, px_poly, py_poly, b_poly, omega, N
):
    x = symbols("x")  # Symbol for the polynomial variable

    # Shifted x-coordinate by domain generator
    accx_omega_poly = accx_poly.subs(x, omega * x % p)
    accy_omega_poly = accy_poly.subs(x, omega * x % p)

    # X-coordinate constraint c2(x)
    c2 = simplify(
        b_poly
        * (
            (accx_poly - px_poly) ** 2 * (accx_poly + px_poly + accx_omega_poly)
            - (py_poly - accy_poly) ** 2
        )
        + (1 - b_poly) * (accx_omega_poly - accx_poly)
    )

    # Y-coordinate constraint c3(x)
    c3 = simplify(
        b_poly
        * (
            (accx_poly - px_poly) * (accy_omega_poly + accy_poly)
            - (py_poly - accy_poly) * (accx_omega_poly - accx_poly)
        )
        + (1 - b_poly) * (accx_omega_poly - accx_poly)
    )

    return c2, c3


def booleanity_constraint(b_poly):
    x = symbols("x")  # Symbol for the polynomial variable

    # Booleanity constraint
    c4 = simplify(b_poly * (1 - b_poly))
    return c4


def lagrange_basis(index, domain):
    x = symbols("x")
    xi = domain[index]
    basis_poly = 1
    for j in range(len(domain)):
        if j != index:
            basis_poly *= (x - domain[j]) / (xi - domain[j])
    return simplify(basis_poly)


def boundary_constraints(accx_poly, accy_poly, accip_poly, S, R, domain):
    x = symbols("x")

    L0 = lagrange_basis(0, domain)
    LN_4 = lagrange_basis(len(domain) - 4, domain)

    Sx, Sy = S
    Rx, Ry = R

    c5 = simplify(L0 * (accx_poly - Sx) + LN_4 * (accx_poly - Rx - Sx))
    c6 = simplify(L0 * (accy_poly - Sy) + LN_4 * (accy_poly - Ry - Sy))
    c7 = simplify(L0 * accip_poly + LN_4 * (accip_poly - 1))

    return c5, c6, c7


# Agrregation polynomial
def aggregate_constraints(constraints, alpha_coeffs):
    if len(constraints) != len(alpha_coeffs):
        raise ValueError("Number of constraints must match number of coefficients.")

    # Aggregate constraints
    c = sum(alpha * constraint for alpha, constraint in zip(alpha_coeffs, constraints))
    return simplify(c)


#


# Example Usage
def example_usage():
    prover_index = 2
    t = random.randint(1, p - 1)

    bits_vector = generate_bits_vector(prover_index, len(public_keys), t)
    selector_vector = [1 if i == prover_index else 0 for i in range(len(public_keys))]

    # Compute accumulators and binary_vector
    cond_sum_acc = conditional_sum_accumulator(bits_vector, public_keys)

    accx = [point[0] for point in cond_sum_acc]
    accy = [point[1] for point in cond_sum_acc]
    accip = inner_product_accumulator(bits_vector, selector_vector)
    b = generate_bits_vector(prover_index, 5, t)
    px = [point[0] for point in public_keys]
    py = [point[1] for point in public_keys]

    print("b", b)
    print(" ")
    print("accx", accx)
    print(" ")
    print("accy", accy)
    print(" ")
    print("accip", accip)
    print(" ")

    # Interpolate
    s_poly = interpolate(selector_vector, D)
    accip_poly = interpolate(accip, D)
    b_poly = interpolate(b, D)
    accy_poly = interpolate(accy, D)
    accx_poly = interpolate(accx, D)
    px_poly = interpolate(px, D)
    py_poly = interpolate(py, D)
    print("accx_poly", accx_poly)
    print(" ")

    print("px_poly:", px_poly)
    print(" ")
    print("py_poly:", py_poly)
    print(" ")
    print("s_poly", s_poly)
    print(" ")

    print("b_poly", b_poly)
    print(" ")
    print("accx_poly", accx_poly)
    print(" ")
    print("accy_poly", accy_poly)
    print(" ")
    print("accip_poly", accip_poly)

    # PCS Commitment
    srs = [pow(omega, i, p) for i in range(N)]  # Simulated SRS setup

    Cb = pcs_commit(b_poly, srs)
    Caccx = pcs_commit(accx_poly, srs)
    Caccy = pcs_commit(accy_poly, srs)
    Caccip = pcs_commit(accip_poly, srs)

    print("Cb:", Cb)
    print(" ")
    print("Caccx:", Caccx)
    print(" ")
    print("Caccy", Caccy)
    print(" ")
    print("Caccip:", Caccip)
    print(" ")

    # constraints
    c1x = inner_product_constraint(accip_poly, b_poly, s_poly, omega, N)
    print("c1x", c1x)
    print(" ")
    c2x, c3x = conditional_addition_constraints(
        accx_poly, accy_poly, px_poly, py_poly, b_poly, omega, N
    )
    print("c4x", c2x)
    print(" ")
    print("c3x", c3x)
    print(" ")
    c4x = booleanity_constraint(b_poly)

    # Expecgted Result Delta From The Seed Point
    R_point = R_expected_result_delta.compute_conditional_sum(
        b, public_keys, Seed_point, p
    )

    print("c4x", c4x)
    print(" ")
    c5x, c6x, c7x = boundary_constraints(
        accx_poly, accy_poly, accip_poly, Seed_point, R_point, D
    )
    print("c5x", c5x)
    print(" ")
    print("c6x", c6x)
    print(" ")
    print("c7x:", c7x)
    print(" ")
    print(type(c7x))
    print(" ")
    hashed_val = Fiat_shamir.fiat_shamir_hash(Cb, Caccip, Caccx, Caccy)
    alpha_list = Fiat_shamir.split_hash_into_chunks(hashed_val)
    cx = Fiat_shamir.construct_the_aggregated_polynomial(
        alpha_list, c1x, c2x, c3x, c4x, c5x, c6x, c7x
    )
    print("Aggregated Cx:", cx)
    print(" ")
    c_poly = simplify(cx)
    q_poly = Quotient_Polyomial_implementation.quotient_polynomial(c_poly, N)
    print("q_poly:", q_poly)
    print(" ")
    cq = pcs_commit(q_poly, srs)
    print("Cq:", cq)
    print(" ")
    Evoluation_hash = Fiat_shamir.fiat_shamir_hash(cq)
    Evolution_point = Fiat_shamir.split_hash_into_chunks(Evoluation_hash, 1)[0]
    print(Evolution_point)
    print(" ")
    px_zeta = Relevant_polynomial_Evoluation.evaluate_polynomials(
        px_poly, Evolution_point
    )
    py_zeta = Relevant_polynomial_Evoluation.evaluate_polynomials(
        py_poly, Evolution_point
    )
    s_zeta = Relevant_polynomial_Evoluation.evaluate_polynomials(
        s_poly, Evolution_point
    )
    b_zeta = Relevant_polynomial_Evoluation.evaluate_polynomials(
        b_poly, Evolution_point
    )
    accip_zeta = Relevant_polynomial_Evoluation.evaluate_polynomials(
        accip_poly, Evolution_point
    )
    accx_zeta = Relevant_polynomial_Evoluation.evaluate_polynomials(
        accx_poly, Evolution_point
    )
    accy_zeta = Relevant_polynomial_Evoluation.evaluate_polynomials(
        accy_poly, Evolution_point
    )
    print("px_zeta", px_zeta)
    print(" ")
    print("py_zeta", py_zeta)
    print(" ")
    print("s_zeta", s_zeta)
    print(" ")
    print("s_zeta", b_zeta)
    print(" ")
    print("s_zeta", accip_zeta)
    print(" ")
    print("s_zeta", accx_zeta)
    print(" ")
    print("s_zeta", accy_zeta)
    print()

    ############

    l_zeta_omega, l_poly = Linearization_polynomial.linearization_polynomial(
        Evolution_point,
        omega,
        accip_poly,
        accx_poly,
        accy_poly,
        px_zeta,
        py_zeta,
        b_zeta,
        alpha_list[:3],
        N,
        p,
    )
    print(" ")
    print(l_zeta_omega, l_poly)

    v_list = Fiat_shamir.fiat_shamir_hash(
        px_zeta, py_zeta, s_zeta, b_zeta, accip_zeta, accx_zeta, accy_zeta, l_zeta_omega
    )
    v_chunks = Fiat_shamir.split_hash_into_chunks(v_list, 8)

    print("v_chunks:", v_chunks)
    print()

    agg_x = Fiat_shamir.construct_the_agg_x(
        v_chunks,
        px_poly,
        py_poly,
        s_poly,
        b_poly,
        accip_poly,
        accx_poly,
        accy_poly,
        q_poly,
    )
    print("agg_x:", agg_x)
    print()

    zeta_omega = Evolution_point * omega % p
    x = symbols("x")
    phi_zeta = agg_x.subs(x, Evolution_point)
    print(phi_zeta)
    print()

    phi_zeta_omega = l_poly.subs(x, zeta_omega)
    print(phi_zeta_omega)

    phi = [
        Cb,
        Caccip,
        Caccx,
        Caccy,
        px_poly,
        py_poly,
        s_zeta,
        b_zeta,
        accip_zeta,
        accx_zeta,
        accy_zeta,
        cq,
        l_zeta_omega,
        phi_zeta,
        phi_zeta_omega,
    ]
    print("Generating Proof...")
    print("Proof :", phi)


if __name__ == "__main__":
    example_usage()
