

from sympy import symbols, simplify
from sympy.integrals.prde import zeros


def linearization_polynomial(zeta, omega, accip_poly, accx_poly, accy_poly, px_zeta, py_zeta, b_zeta, alpha_coeffs,N,p):
    x = symbols('x')
    l1 = simplify((zeta - omega ** (N - 4)) * accip_poly)
    l2 = simplify((zeta - omega ** (N - 4)) * (b_zeta * (accx_poly - px_zeta)**2 * accx_poly + (1 - b_zeta) * accy_poly))
    l3 = simplify((zeta - omega ** (N - 4)) * ((b_zeta * (accx_poly - px_zeta) + 1 - b_zeta) * accx_poly + b_zeta * (accx_poly - px_zeta) * accy_poly))

    l_poly = simplify(alpha_coeffs[0] * l1 + alpha_coeffs[1] * l2 + alpha_coeffs[2] * l3)
    zeta_omega = zeta * omega % p
    l_zeta_omega = l_poly.subs(x, zeta_omega)
    return l_zeta_omega, l_poly


def main():

    zeta =48635463943209834798109814161294753926839975257569795305637098542720658922315
    omega =49307615728544765012166121802278658070711169839041683575071795236746050763237
    accip_poly =179*2**7+2321*2**6
    accx_poly =295*2**7+ 3319*2**6
    accy_poly =2**2+9*3
    px_zeta =10
    py_zeta =11
    b_zeta =12
    alpha_c =[1,2,3,4]
    linearization_polynomial(zeta,omega,accip_poly,accx_poly,accy_poly,px_zeta,py_zeta,b_zeta,alpha_c)
