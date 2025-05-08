# from jam.ring_vrf.ring_proof.KZG_poly_affine_powers_of_tau import commit_to_polynomial
from py_ecc.optimized_bls12_381 import normalize

from jam.ring_vrf.ring_proof.constants import omega, S_PRIME, Blinding_Base, PaddingPoint, S_ORDER, Max_ring_size, \
    SeedPoint
from jam.ring_vrf.ring_proof.get_ring_points import pk_x_y_list, secret_t
from jam.ring_vrf.ring_proof.helpers import unzip
from jam.ring_vrf.ring_proof.poly_interpolation_fft import fft, poly_interpolate_fft
from jam.ring_vrf.ring_proof.short_weierstrass import twisted_edward_to_sw
from jam.ring_vrf.ring_proof.short_weierstrass_curve_ops import point_multiplication, point_addition
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import commit_to_polynomial
from jam.ring_vrf.ring_proof.constants import SIZE as size

# H's Scaled Multiples
def h_vector(Blinding_Base,size=512):
    """
    input: Blinding Base
    output:H_Vector
    """
    #convert B_B into SW point
    sw_B_B= twisted_edward_to_sw(Blinding_Base)
    H_Vct = []
    for i in range(size):
        New_H_point = point_multiplication(2**i, sw_B_B)
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
    N_K=Max_ring_size #len(Ring_of_pk) #255

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
    sw_H= twisted_edward_to_sw(H)
    Pk=Ring_of_pk[k]
    R=point_addition(Pk, point_multiplication(t, sw_H))
    return R



def interpolation_to_resulting_vectors(x_vector,omega):
    """
    input: Domain_vector, other vector
    output: Interpolated poly
    """
    interpolated_poly=poly_interpolate_fft(x_vector,omega,S_PRIME)
    return interpolated_poly


def commitment_to_constructed_vectors(polynomial):
    """
    input: polynomial with coeffs
    output: commitment to the poly coeffs
    """

    poly_commitment= commit_to_polynomial(polynomial)
    return poly_commitment

def pad_padding_point(int_pk_ring,padding_element):
    padding_element=twisted_edward_to_sw(padding_element)
    for i in range(len(int_pk_ring),Max_ring_size):
        int_pk_ring.append(padding_element)
    return  int_pk_ring



Ring_of_pk=pk_x_y_list

Result_point=relation_to_prove(3,secret_t,Blinding_Base,Ring_of_pk)
print("Result Point",Result_point)
Result_plus_Seed=point_addition(Result_point, twisted_edward_to_sw(SeedPoint))

print("Result_plus_seed:", Result_plus_Seed)
print("seed sw:", twisted_edward_to_sw(SeedPoint))
max_ring_pk=pad_padding_point(Ring_of_pk,PaddingPoint)

H_vector=h_vector(Blinding_Base)
# print("H_vector",H_vector)

pre_pd_pk_ring = public_intput_preprocessing(max_ring_pk, H_vector)
# print("p after preprocessing:")
# print("p_pk_ring",pre_pd_pk_ring)

px_v,py_v=unzip(pre_pd_pk_ring)

print("px_v",px_v[:],'\n',"py_v",py_v[:])

s_vector=selector_vector(Ring_of_pk,size)
# print("s_vector:",s_vector)

# #interpolation of resulting vectors

import time
start_time= time.time()
px_I=interpolation_to_resulting_vectors(px_v,omega)
py_I=interpolation_to_resulting_vectors(py_v,omega)
s_v_I=interpolation_to_resulting_vectors(s_vector,omega)
print("Interolated_Px",px_I)
print("is Evaluations valid:", px_v==fft(px_I,omega,S_PRIME))
print("Interpolated_py",py_I)
print("is Evaluations valid:",py_v==fft(py_I,omega,S_PRIME))
print("Interpolated_s",s_v_I)
print("is Evaluations valid:",s_vector==fft(s_v_I,omega,S_PRIME))

end_time=time.time()
print("interpolation_time:",end_time - start_time)

start_time=time.time()
C_px=commitment_to_constructed_vectors(px_I)
C_py=commitment_to_constructed_vectors(py_I)
C_s=commitment_to_constructed_vectors(s_v_I)

end_time=time.time()

print(normalize(C_px),'\n',normalize(C_py),'\n',normalize(C_s))
print("commitment time:", end_time -start_time)
