from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchParams
from sympy import mod_inverse
from jam.ring_vrf.ring_proof.constants import SeedPoint, PaddingPoint, Blinding_Base, S_A, S_B, S_PRIME


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
    mont_x=(1+y) * mod_inverse(1-y,S_PRIME) % S_PRIME

    mont_y= (1+y)* mod_inverse(x- (x* y),S_PRIME) % S_PRIME
    return  int(mont_x),int(mont_y)


def mont_to_short_weierstrass(mont_point):
    # // ((x + A / 3) / B, y / B)
    x,y=mont_point
    x_sw= (x +  mont_a % S_PRIME * mod_inverse(3,S_PRIME) %S_PRIME )* mod_inverse(mont_b,S_PRIME) %S_PRIME
    y_sw=y* mod_inverse(mont_b,S_PRIME)% S_PRIME
    return int(x_sw),int(y_sw)


def is_on_weierstrass(point):
    x,y=point
    #y^2=x^3+a*x+b
    lhs=pow(y,2,S_PRIME)
    rhs=(pow(x,3,S_PRIME) + S_A * x  % S_PRIME + S_B % S_PRIME) % S_PRIME
    return lhs==rhs


def is_on_monty(point):
    x,y=point
    # B*y**2=x**3+a*x**2+x
    lhs= mont_b *pow(y,2,S_PRIME) % S_PRIME
    rhs= (pow(x,3,S_PRIME) % S_PRIME + mont_a *pow(x,2,S_PRIME) % S_PRIME +x % S_PRIME ) % S_PRIME
    return lhs==rhs

##SHORT WEIERSTRASS TO TWISTED_EDWARD##

def short_ws_to_monty(sw_point):
    ws_x,ws_y=sw_point
    # (Bx - A / 3, By)
    mont_x= (mont_b* ws_x % S_PRIME - mont_a *mod_inverse(3,S_PRIME)) % S_PRIME
    mont_y= mont_b * ws_y % S_PRIME
    return int(mont_x),int(mont_y)


def monty_to_twisted_edward(mont_point):#(x, y) -> (x / y, (x−1) / (x + 1))
    mont_x,mont_y=mont_point
    te_x= mont_x * mod_inverse(mont_y,S_PRIME) % S_PRIME
    te_y= (mont_x -1) * mod_inverse(mont_x+1,S_PRIME) % S_PRIME
    return int(te_x),int(te_y)


def short_to_te(sw_point):
    mont_point= short_ws_to_monty(sw_point)
    # print(mont_point)
    te_point=monty_to_twisted_edward(mont_point)
    return  te_point

