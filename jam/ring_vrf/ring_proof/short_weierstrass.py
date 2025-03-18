from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchParams
from sympy import mod_inverse
from jam.ring_vrf.ring_proof.constants import SeedPoint, PaddingPoint, Blinding_Base

# from jam.ring_vrf.ring_proof.short_weierstrass_curve_ops import point_multiplication

# from jam.ring_vrf.ring_proof.short_weierstrass_curve_ops import point_addition, point_multiplication, point_doubling

S_PRIME_FIELD=BandersnatchParams.PRIME_FIELD

mont_a=29978822694968839326280996386011761570173833766074948509196803838190355340952#2*(BandersnatchParams.EDWARDS_A + BandersnatchParams.EDWARDS_D) % BandersnatchParams.ORDER * mod_inverse(BandersnatchParams.EDWARDS_A-BandersnatchParams.EDWARDS_D, BandersnatchParams.PRIME_FIELD) % BandersnatchParams.ORDER

mont_b=25465760566081946422412445027709227188579564747101592991722834452325077642517 #4*mod_inverse(BandersnatchParams.EDWARDS_A-BandersnatchParams.EDWARDS_D,BandersnatchParams.PRIME_FIELD)


###Twisted Edward Curve to Short Weierstrass##

def twisted_edward_to_sw(point):
    mont_point=twisted_edward_to_mont(point)
    sw_point=mont_to_short_weierstrass(mont_point)
    return sw_point


def twisted_edward_to_mont(point):
     # (1 + y) / (1 - y), (1 + y) / (x(1 - y))
    """
    input: Twisted Edward point
    output: Montgomery Point
    """
    x,y=point
    mont_x=(1+y) * mod_inverse(1-y,S_PRIME_FIELD) % S_PRIME_FIELD

    mont_y= (1+y)* mod_inverse(x- (x* y),S_PRIME_FIELD) % S_PRIME_FIELD
    return  mont_x,mont_y



ws_a=10773120815616481058602537765553212789256758185246796157495669123169359657269
ws_b=29569587568322301171008055308580903175558631321415017492731745847794083609535


def mont_to_short_weierstrass(mont_point):
    # // ((x + A / 3) / B, y / B)
    x,y=mont_point
    x_sw= (x +  mont_a % S_PRIME_FIELD * mod_inverse(3,S_PRIME_FIELD) %S_PRIME_FIELD )* mod_inverse(mont_b,S_PRIME_FIELD) %S_PRIME_FIELD
    y_sw=y* mod_inverse(mont_b,S_PRIME_FIELD)% S_PRIME_FIELD
    return x_sw,y_sw


def is_on_weierstrass(point):
    x,y=point
    #y^2=x^3+a*x+b
    lhs=pow(y,2,S_PRIME_FIELD)
    rhs=(pow(x,3,S_PRIME_FIELD) + ws_a * x  % S_PRIME_FIELD + ws_b % S_PRIME_FIELD) % S_PRIME_FIELD
    # print("weierstrass:")
    # print(lhs)
    # print(rhs)
    # print(lhs>S_PRIME_FIELD)
    # print(rhs>S_PRIME_FIELD)
    return lhs==rhs


def is_on_monty(point):
    x,y=point
    # B*y**2=x**3+a*x**2+x
    lhs= mont_b *pow(y,2,S_PRIME_FIELD) % S_PRIME_FIELD
    rhs= (pow(x,3,S_PRIME_FIELD) % S_PRIME_FIELD + mont_a *pow(x,2,S_PRIME_FIELD) % S_PRIME_FIELD +x % S_PRIME_FIELD ) % S_PRIME_FIELD
    # print("monty:")
    # print(lhs>S_PRIME_FIELD)
    # print(rhs>S_PRIME_FIELD)
    # print(lhs)
    # print(rhs)
    return lhs==rhs




# print(PaddingPoint)
# print("TE_2_Mont:",twisted_edward_to_mont(PaddingPoint))
# print("IS ON MONTY:",is_on_monty(twisted_edward_to_mont(PaddingPoint)))
# print(twisted_edward_to_sw(PaddingPoint))
# print("IS ON SW:",is_on_weierstrass(twisted_edward_to_sw(PaddingPoint)))



##SHORT WEIERSTRASS TO TWISTED_EDWARD##

def short_ws_to_monty(sw_point):
    ws_x,ws_y=sw_point
    # (Bx - A / 3, By)
    mont_x= (mont_b* ws_x % S_PRIME_FIELD - mont_a *mod_inverse(3,S_PRIME_FIELD)) % S_PRIME_FIELD
    mont_y= mont_b * ws_y % S_PRIME_FIELD
    return mont_x,mont_y


def monty_to_twisted_edward(mont_point):#(x, y) -> (x / y, (x−1) / (x + 1))
    mont_x,mont_y=mont_point
    te_x= mont_x * mod_inverse(mont_y,S_PRIME_FIELD) % S_PRIME_FIELD
    te_y= (mont_x -1) * mod_inverse(mont_x+1,S_PRIME_FIELD) % S_PRIME_FIELD
    return te_x,te_y


def short_to_te(sw_point):
    mont_point= short_ws_to_monty(sw_point)
    te_point=monty_to_twisted_edward(mont_point)
    return  te_point




# print(twisted_edward_to_sw(Blinding_Base))
# print(twisted_edward_to_sw(PaddingPoint))
# print(twisted_edward_to_sw(SeedPoint))


#
# print("Padding_point",PaddingPoint)
# print("TO SW",twisted_edward_to_sw(PaddingPoint))
# print("is on monty:",is_on_monty(twisted_edward_to_mont(PaddingPoint)))
# print("is on weierstrass:",is_on_weierstrass(twisted_edward_to_sw(PaddingPoint)))
#
# print("TO TE",short_to_te((twisted_edward_to_sw(PaddingPoint))))
# print("is on monty:", is_on_monty(short_ws_to_monty(twisted_edward_to_sw(PaddingPoint))))
# print("is same:",short_to_te((twisted_edward_to_sw(PaddingPoint)))==PaddingPoint)
# print(S_PRIME_FIELD)
#
# print(0x4247698f4e32ad45a293959b4ca17afa4a2d2317e4c6ce5023e1fd63d1b5de98)
#
# print(0x300c3385d13bedb7c9e229e185c4ce8b1dd3b71366bb97c30855c0aa41d62727)
#
#
# print("Pont_Addition:",point_addition(twisted_edward_to_sw(SeedPoint),twisted_edward_to_sw(PaddingPoint)))
#
# # print(point_addition(SeedPoint,PaddingPoint))
#
# # print(short_to_te((12954616677420236926222952785603269645790775774441715450822160404842410846770, 11424733789376569733845001755790233162374185428666073594796525539674801483128)
# # ))
#
# print(twisted_edward_to_sw((23085768010608148908463662140689848067024076940671416153027483252777019931540, 37130114727445837959967920519999914008769419672480317539580862224934694126365)
# ))
# print(is_on_weierstrass(twisted_edward_to_sw(SeedPoint)))
# p_m_v=point_multiplication(2,SeedPoint)
# print(is_on_weierstrass(p_m_v))

