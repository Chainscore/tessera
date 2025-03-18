from sympy import expand
import random
from jam.ring_vrf.ring_proof.helpers import unzip, do_modulus
from jam.ring_vrf.ring_proof.preprocessing import D, p_pk_ring, s_vector
from jam.ring_vrf.ring_proof.short_weierstrass import short_to_te
from jam.ring_vrf.ring_proof.constants import S_ORDER, SeedPoint
from jam.ring_vrf.ring_proof import short_weierstrass_curve_ops as sw
from jam.ring_vrf.ring_proof.polynomial_interpolation import polynomial_interpolation, check_is_valid
from jam.ring_vrf.ring_proof.KZG_polynomial_commit_open_verify import commit_to_polynomial


def bits_vector(k,t,ring_size=5,size=10):
    """"
    input: k -position of the public key in the ring,
           t- secret scalr

    output:a binary vector
    """
    t_vector=bin(t)[2:]
    t_little=t_vector[::-1]
    pad=0
    b_vector=[]

    for i in range(1,ring_size+1):
        if i==k:
            b_vector.append(1)
        else:
            b_vector.append(0)

    for i in t_little[:size-ring_size]:
        b_vector.append(int(i))

    b_vector.append(pad)
    return b_vector

# print(bits_vector(3,14))


def conditional_sum_accumulator(seed_point,bits_vector,Ring_of_P,size=10):
    """
    input: bits_vector,Ring_of_P
    output: accx, accy
    """
    seed_point_sw=short_to_te(seed_point)
    acc = [seed_point_sw]
    for i in range(size-4):

        if bits_vector[i]==0:
            new_val=acc[-1]
        else:
            new_val = sw.point_addition(acc[-1],Ring_of_P[i])
        acc.append(new_val)
    return unzip(acc)


def inner_product_accumulator(bits_vector,selector_vector,size=10):
    """"
    input:bits_vector, selector_vector
    output: inner_product_accumulator
    """
    accip=[0]
    for i in range(size-4):
        new_val =accip[-1] + bits_vector[i] * selector_vector[i]
        accip.append(new_val)
    return accip


def interpolate(D,x_vector):
    """
        input: A vector , 3 random values
        output: interpolated polynomial
    """
    for i in range(3):
        x_vector.append(random.randint(1,S_ORDER))
    poly=polynomial_interpolation(D,x_vector)
    return do_modulus(poly)


def commitment(interpolated_polynomial):

    """"
    input: interpolated polynomial
    output: commitment for the polynomial
    """

    cmt=commit_to_polynomial(interpolated_polynomial)
    return cmt


b_v=bits_vector(3,21)
b_v=b_v[:7]
acc_x,acc_y=conditional_sum_accumulator(SeedPoint,b_v,p_pk_ring)
acc_ip=inner_product_accumulator(b_v,s_vector)


# print(len(b_v))
# print(len(acc_y))
# print(len(acc_x))
# print(len(acc_ip))
# print(len(D))

b_v_I=interpolate(D,b_v)
acc_x_I=interpolate(D,acc_x)
acc_y_I=interpolate(D,acc_y)
acc_ip_I=interpolate(D,acc_ip)

print(b_v_I)
print(acc_x_I)
print(acc_y_I)
print(acc_ip_I)
print(check_is_valid(b_v_I,D,b_v))
print(check_is_valid(acc_x_I,D,acc_x))
print(check_is_valid(acc_y_I,D,acc_y))
print(check_is_valid(acc_ip_I,D,acc_ip))

#Commitments as Affine Co-ordinates
C_b_v=commitment(b_v_I)
C_acc_x=commitment(acc_x_I)
C_acc_y=commitment(acc_y_I)
C_acc_ip=commitment(acc_ip_I)


# print(C_b_v)
# print(C_acc_x)
# print(C_acc_y)
# print(C_acc_ip)

















# print(interpolate(px))
#
# print(interpolate(py))
#
# print("px_commitment:",commitement(interpolate(px)))
# print("py_commitment:",commitement(interpolate(py)))


# print(interpolate(D))
# print(interpolate(bits_vector(3,random.randint(1,S_ORDER))))
#

















# secret_scalr=bytes.fromhex("3d6406500d4009fdf2604546093665911e753f2213570a29521fd88bc30ede18")
# secret_t=int.from_bytes(secret_scalr,'little')
#
#
# b_v=bits_vector(3,secret_t)
# Selector_Vector= [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#
# print("BITS VECTOR:",b_v)
# print(len(b_v))
#
# print("inner_product accumulator:",inner_product_accumulator(b_v,Selector_Vector))
# print("conditional sum accumulator:",conditional_sum_accumulator(SeedPoint,b_v,Ring_of_pk))
# print(twisted_edward_to_sw(SeedPoint))
#
# print(point_addition((0, 11982629110561008531870698410380659621661946968466267969586599013782997959645),Ring_of_pk[0]))














#
# print()
# print("PK_STRINGS")
# pk_ring="7b32d917d5aa771d493c47b0e096886827cd056c82dbdba19e60baa8b2c60313d3b1bdb321123449c6e89d310bc6b7f654315eb471c84778353ce08b951ad471561fdb0dcfb8bd443718b942f82fe717238cbcf8d12b8d22861c8a09a984a3c59d97151298a5339866ddd3539d16696e19e6b68ac731562c807fe63a1ca495064fd11f89c2a1aaefe856bb1c5d4a1fad73f4de5e41804ca2c17ba26d6e10050c86d06ee2c70da6cf2da2a828d8a9d8ef755ad6e580e838359a10accb086ae437ad6fdeda0dde0a57c51d3226b87e3795e6474393772da46101fd597fbd456c1b3f9dc0c4f67f207974123830c2d66988fb3fb44becbbba5a64143f376edc51d9"
# pk_list=[]
# pk_x_y_list=[]
# pk_x_list=[]
# frm=0
# to=64
# print(len(pk_ring))
# for i in range(len(pk_ring)//64):
#     pk_list.append(pk_ring[frm:to])
#     frm=to
#     to+=64
# print(pk_list)
# sample="355788aa5f7bdf89352c957833b217c025a43f96ec996d0f4c5f90cab6457f1e"
# print(len(sample))
# count=0
# for string in pk_list:
#     try:
#         pk=BandersnatchPoint.string_to_point(string)
#         pk_x_y_list.append((pk.x, pk.y))
#         print(pk)
#         pk_x_list.append(pk.x)
#         print(pk.is_on_curve())
#
#
#     except ValueError as e:
#         count+=1
# print("p_x_y_list",pk_x_y_list)
# print(count)
# block_producer="9d97151298a5339866ddd3539d16696e19e6b68ac731562c807fe63a1ca49506"
# print('b_p in pk_list:',block_producer in pk_list, pk_list.index(block_producer))
# print(pk_x_list)
#
#
# print("RING_PROOF_STRINGS")
# print()
# ring_pk_proof="98bc465cdf55ee0799bc25a80724d02bb2471cd7d065d9bd53a3a7e3416051f6e3686f7c6464c364b9f2b0f15750426a9107bd20fe94a01157764aab5f300d7e2fcba2178cb80851890a656d89550d0bebf60cca8c23575011d2f37cdc06dcdd93818c0c1c3bff5a793d026c604294d0bbd940ec5f1c652bb37dc47564d71dd1aa05aba41d1f0cb7f4442a88d9b533ba8e4788f711abdf7275be66d45d222dde988dedd0cb5b0d36b21ee64e5ef94e26017b674e387baf0f2d8bd04ac6faab057510b4797248e0cb57e03db0199cd77373ee56adb7555928c391de794a07a613f7daac3fc77ff7e7574eaeb0e1a09743c4dae2b420ba59cf40eb0445e41ffb2449021976970c858153505b20ac237bfca469d8b998fc928e9db39a94e2df1740ae0bad6f5d8656806ba24a2f9b89f7a4a9caef4e3ff01fec5982af873143346362a0eb9bb2f6375496ff9388639c7ffeb0bcee33769616e4878fc2315a3ac3518a9da3c4f072e0a0b583436a58524f036c3a1eeca023598682f1132485d3a57088b63acd86c6c72288568db71ff15b7677bfe7218acdebb144a2bf261eb4f65980f830e77f37c4f8d11eac9321f302a089698f3c0079c41979d278e8432405fc14d80aad028f79b0c4c626e4d4ac4e643692a9adfdc9ba2685a6c47eef0af5c8f5d776083895e3e01f1f944cd7547542b7e64b870b1423857f6362533f7cd2a01d231ffed60fe26169c28b28ace1a307fdc8d4b29f0b44659402d3d455d719d896f83b7ee927f0652ca883e4cfa85a2f4f7bc60dda1b068092923076893db5bd477fa2d26173314d7512760521d6ec9f"
# print(len(ring_pk_proof)//64)
# ring_proof_list=[]
# frm=0
# to=64
# for i in range(len(ring_pk_proof)//64):
#     ring_proof_list.append(ring_pk_proof[frm:to])
#     frm=to
#     to+=64
# print(ring_proof_list)
# cnt=0
# for string in ring_proof_list:
#     try:
#         relative_point=BandersnatchPoint.string_to_point(string)
#         print(relative_point)
#         print(relative_point.is_on_curve())
#     except ValueError as e:
#         print(ring_proof_list.index(string)+1)
#         cnt+=1
#
# print(cnt)

