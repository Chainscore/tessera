from jam.ring_vrf.ring_proof.constants import omega, S_PRIME, Blinding_Base, PaddingPoint, S_ORDER, Max_ring_size
from sympy import  symbols
from jam.ring_vrf.ring_proof.get_ring_points import pk_x_y_list, secret_t
from jam.ring_vrf.ring_proof.helpers import unzip, do_modulus
from jam.ring_vrf.ring_proof.polynomial_interpolation import polynomial_interpolation
from jam.ring_vrf.ring_proof.short_weierstrass import twisted_edward_to_sw, is_on_monty, is_on_weierstrass
from jam.ring_vrf.ring_proof.short_weierstrass_curve_ops import point_multiplication, point_addition
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import commit_to_polynomial
from jam.ring_vrf.ring_proof.constants import SIZE as S

from jam.ring_vrf.ring_proof.constants import D
size=S


# H's Scaled Multiples
def h_vector(Blinding_Base,size=512):
    """
    input: Blinding Base
    output:H_Vector
    """
    #convert B_B into SW point
    Blinding_Base= twisted_edward_to_sw(Blinding_Base)
    H_Vct = []
    for i in range(size):
        New_H_point = point_multiplication(2**i, Blinding_Base)
        H_Vct.append(New_H_point)
    return H_Vct

# H_vector=h_vector(Blinding_Base)

# Public input preprocessing
def public_intput_preprocessing(Ring_of_pkeys, H_Vector,size=512):
    """
    input: Public keys ring,  pedersen blinding base
    output: Px,Py
    """
    for i in range(0,size-4-len(Ring_of_pkeys)):
        Ring_of_pkeys.append(H_Vector[i])

    for i in range(4):
        Ring_of_pkeys.append((0,0))

    return Ring_of_pkeys



# selector vector
def selector_vector(Ring_of_pk,size=512):
    """
    input: ring of public key's
    output: selecting vector having 0/1
    """
    s_vector = []
    N_K=Max_ring_size #len(Ring_of_pk)

    for i in range(size):
        if i<N_K:
            s_vector.append(1)
        else:
            s_vector.append(0)

    return s_vector


def relation_to_prove(k,t,H,Ring_of_pk):
    """
    input:Prover Secret Scalar, Prover index, Blinding Base, Ring_of_pk
    """
    Pk=Ring_of_pk[k]
    R=point_addition(Pk, point_multiplication(t, H))
    return R



def interpolation_to_resulting_vectors(D, x_vector):
    """
    input: Domain_vector, other vector
    output: Interpolated poly
    """

    interpolated_poly=polynomial_interpolation(D,x_vector)
    return interpolated_poly


def commitment_to_constructed_vectors(polynomial):
    """
    input: polynomial with coeffs
    output: commitment to the poly coeffs
    """

    poly_commitment= commit_to_polynomial(polynomial)
    return poly_commitment



Ring_of_pk=pk_x_y_list

Result_point=relation_to_prove(3,secret_t,Blinding_Base,Ring_of_pk)
# print("Result Point",Result_point)

H_vector=h_vector(Blinding_Base)
print("H_vector",H_vector)

pre_pd_pk_ring = public_intput_preprocessing(Ring_of_pk, H_vector)
# print("p after preprocessing:")
# print("p_pk_ring",pre_pd_pk_ring)

px_v,py_v=unzip(pre_pd_pk_ring)

# print("px_v",px_v[:],'\n',"py_v",py_v[:])

s_vector=selector_vector(Ring_of_pk,size)
print("s_vector:",s_vector)

# #interpolation of resulting vectors

import time
start_time= time.time()
px_I=interpolation_to_resulting_vectors(D,px_v)
py_I=interpolation_to_resulting_vectors(D,py_v)
s_v_I=interpolation_to_resulting_vectors(D,s_vector)

print("Interolated_Px_v",px_I)
end_time=time.time()
print("interpolation_time:",end_time - start_time)

# check whether interpolation is accurate
# print(check_is_valid(px_I,D,px_v))
# print(check_is_valid(py_I,D,py_v))
# print(check_is_valid(s_v_I,D,s_vector))
# print(px_I,'\n',px_I,'\n',s_v_I)
#commitment to constructed vectors

start_time=time.time()
C_px=commitment_to_constructed_vectors(px_I)
C_py=commitment_to_constructed_vectors(py_I)
C_s=commitment_to_constructed_vectors(s_v_I)

print("Commitment of Px_I",C_px)
end_time=time.time()

print("commitment time:", end_time -start_time)

# print(C_px,'\n',C_py,'\n',C_s)

# print(H_vector[0])
# print(twisted_edward_to_sw(PaddingPoint))
# print(is_on_weierstrass(twisted_edward_to_sw(PaddingPoint)))