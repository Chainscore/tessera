from sympy import expand
import random
import time
from jam.ring_vrf.ring_proof.get_ring_points import secret_t
from jam.ring_vrf.ring_proof.helpers import unzip, do_modulus
from jam.ring_vrf.ring_proof.polynomial_interpolation import polynomial_interpolation
from jam.ring_vrf.ring_proof.preprocessing import pre_pd_pk_ring, s_vector
# from jam.ring_vrf.ring_proof.preprocessing import D, p_pk_ring, s_vector
from jam.ring_vrf.ring_proof.short_weierstrass import short_to_te, twisted_edward_to_sw
from jam.ring_vrf.ring_proof.constants import S_ORDER, SeedPoint, S_PRIME, omega, D
from jam.ring_vrf.ring_proof import short_weierstrass_curve_ops as sw
# from jam.ring_vrf.ring_proof.polynomial_interpolation import polynomial_interpolation, check_is_valid
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import commit_to_polynomial

size= 512 #sample size

def bits_vector(k,t,ring_size=255,size=512):
    """"
    input: k -position of the public key in the ring,
           t- secret scalr

    output:a binary vector
    """
    t_vector=bin(t)[2:]
    t_len=len(t_vector)
    print(t_vector)
    t_vector=t_vector[::-1]
    print(t_vector)
    pad_bit=0
    b_vector=[]

    for i in range(ring_size):
        if i==k:
            b_vector.append(1)
        else:
            b_vector.append(0)

    # for i in t_little[:size-ring_size]:
    for i in t_vector:
        b_vector.append(int(i))
    for i in range(len(b_vector),size-4):
        b_vector.append(pad_bit)
    return b_vector
# print(bits_vector(3,14))


def conditional_sum_accumulator(seed_point,bits_vector,Ring_of_P,size=512):
    """
    input: bits_vector,Ring_of_P
    output: accx, accy
    """
    seed_point_sw=twisted_edward_to_sw(seed_point)
    acc = [seed_point_sw]
    for i in range(1,size-4+1):

        if bits_vector[i-1]==0:
            new_val=acc[i-1]
        else:
            new_val = sw.point_addition(acc[i-1],Ring_of_P[i-1])
        acc.append(new_val)
    return unzip(acc)


def inner_product_accumulator(bits_vector,selector_vector,size=512):
    """"
    input:bits_vector, selector_vector
    output: inner_product_accumulator
    """
    accip=[0]
    for i in range(1,size-4+1):
        new_val =accip[i-1] + bits_vector[i-1] * selector_vector[i-1]
        accip.append(new_val)
    print("accip",len(accip))
    return accip[1:]


def interpolate(D,x_vector):
    """
        input: A vector , 3 random values
        output: interpolated polynomial
    """
    for i in range(4):
        x_vector.append(random.randint(1,S_ORDER))
    poly=polynomial_interpolation(D,x_vector)
    return poly


def commitment(interpolated_polynomial):

    """"
    input: interpolated polynomial
    output: commitment for the polynomial
    """

    cmt=commit_to_polynomial(interpolated_polynomial)
    return cmt


b_v=bits_vector(3,secret_t)

print('this len:',len(bin(secret_t).zfill(256)[2:]))
print('b_v',b_v)

b_v_tf=[]
for i in b_v:
    if i==1:
        b_v_tf.append(True)
    else:
        b_v_tf.append(False)


print("b_V TRUE_FALSE_repr:",b_v_tf)
acc_x,acc_y=conditional_sum_accumulator(SeedPoint,b_v,pre_pd_pk_ring)
acc_ip=inner_product_accumulator(b_v,s_vector)
print("accx:",acc_x)
print("accy:",acc_y)
print("acc_ip",acc_ip)



start_time=time.time()
b_v_I=interpolate(D,b_v)
acc_x_I=interpolate(D,acc_x)
acc_y_I=interpolate(D,acc_y)
acc_ip_I=interpolate(D,acc_ip)

print("Interpolated:",b_v_I)
end_time=time.time()
print("interpolation time:",end_time-start_time)


# print(acc_y_I)
# print(acc_ip_I)

#check the validity
# print(check_is_valid(b_v_I,D,b_v))
# print(check_is_valid(acc_x_I,D,acc_x))
# print(check_is_valid(acc_y_I,D,acc_y))
# print(check_is_valid(acc_ip_I,D,acc_ip))


stat_time=time.time()
# Commitments as Affine Co-ordinates
C_b_v=commitment(b_v_I)
C_acc_x=commitment(acc_x_I)
C_acc_y=commitment(acc_y_I)
C_acc_ip=commitment(acc_ip_I)

print("commitment to bits_poly:",C_b_v)
end_time=time.time()
print("commitment time:", end_time - start_time)



