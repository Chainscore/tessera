from sympy import mod_inverse
from jam.ring_vrf.ring_proof.constants import S_PRIME as S_PRIME_FIELD, PaddingPoint, Blinding_Base
from jam.ring_vrf.ring_proof.constants import S_A,SeedPoint,S_ORDER
from jam.ring_vrf.ring_proof.short_weierstrass import is_on_weierstrass, twisted_edward_to_sw


def point_addition(point1, point2):
    """
    input: point1 and point2
    output: Point addition
    """
    # If one of the points is the identity, return the other.
    if point1 is None:
        return point2
    if point2 is None:
        return point1
    # Otherwise, do the normal point addition (using the curve's parameters).
    x1, y1 = point1
    x2, y2 = point2
    if x1 == x2 and y1 == y2:
        return point_doubling(point1)
    lam = (y2 - y1) * mod_inverse(x2 - x1, S_PRIME_FIELD) % S_PRIME_FIELD
    x3 = (lam * lam - x1 - x2) % S_PRIME_FIELD
    y3 = (lam * (x1 - x3) - y1) % S_PRIME_FIELD
    return (x3, y3)


def point_multiplication(k, point):
    """
    input: point P, scalr k
    output: point multiplication.
    """
    result = None  # Identity (0,1,0: Projective)
    addend = point
    while k:
        if k & 1:
            result = point_addition(result, addend)
        addend = point_doubling(addend)
        k >>= 1
    return result


def point_doubling(point):
    """
    input: point
    output: doubled point
    """
    #need Short Weierstrass A,B constants(satisfied)
    x1,y1=point
    x1=int(x1)
    y1=int(y1)
    slope=(3* x1**2 % S_PRIME_FIELD + S_A  % S_PRIME_FIELD)* mod_inverse(2*y1,S_PRIME_FIELD) % S_PRIME_FIELD
    x3=(pow(slope,2, S_PRIME_FIELD) - 2*x1 % S_PRIME_FIELD) % S_PRIME_FIELD
    y3=(slope*(x1-x3) % S_PRIME_FIELD -y1) % S_PRIME_FIELD
    # print(y3>S_PRIME_FIELD)
    # print(x3>S_PRIME_FIELD)
    return x3,y3





# sp=SeedPoint
# SeedPoint= twisted_edward_to_sw(SeedPoint)
# Blinding_Base= twisted_edward_to_sw(Blinding_Base)
# print(is_on_weierstrass(point_addition(SeedPoint,Blinding_Base)))
# print(is_on_weierstrass(twisted_edward_to_sw(PaddingPoint)))
# print(is_on_weierstrass(point_multiplication(S_PRIME_FIELD,SeedPoint)))
# print()







# print(short_to_te(SeedPoint)==sp)
# print("doubling:",is_on_weierstrass(point_doubling(SeedPoint)))
#
# print(Blinding_Base)
# print(is_on_weierstrass(point_doubling(Blinding_Base)))
# print(is_on_weierstrass(point_doubling(SeedPoint)))

# print(is_on_weierstrass(point_addition(SeedPoint,Blinding_Base)))
#
# print(SeedPoint)
#
# print("BB",is_on_weierstrass(Blinding_Base))
# print(point_addition(SeedPoint,Blinding_Base))