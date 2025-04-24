import time
from jam.ring_vrf.ring_proof.constants import S_PRIME, SeedPoint, omega, D, SIZE
from jam.ring_vrf.ring_proof.poly_interpolation_fft import fft, poly_mul_fft
from jam.ring_vrf.ring_proof.polynomial_interpolation import poly_subtract, poly_multiply, represent_as_poly,poly_add
from jam.ring_vrf.ring_proof.preprocessing import px_I, py_I, s_v_I, Result_point, Result_plus_Seed
from jam.ring_vrf.ring_proof.prover_witness_polynomials import acc_x_I,acc_y_I,b_v_I,acc_ip_I
from jam.ring_vrf.ring_proof.polynomial_interpolation import lagrange_basis_polynomial
from jam.ring_vrf.ring_proof.short_weierstrass import twisted_edward_to_sw
# from jam.ring_vrf.ring_proof.prover_witness_polynomials import acc_x
# from jam.ring_vrf.ring_proof.short_weierstrass import twisted_edward_to_sw
from sympy import symbols
x=symbols('x')
start_time=time.time()

def inner_product_contraint_poly(accip_x,b_x,s_x):
    # Define symbols
    accip_omega_x=[accip_x[i]*(omega**i) % S_PRIME for i in range(len(accip_x))]

    #Compute constraint polynomial
    constraint = poly_subtract(poly_subtract(accip_omega_x ,accip_x,S_PRIME) ,
                               poly_multiply(b_x,s_x,S_PRIME ),S_PRIME)

    # constraint_n=poly_subtract(poly_subtract(accip_omega_x ,accip_x,S_PRIME) ,
    #                            poly_mul_fft(b_x,s_x,S_PRIME ),S_PRIME)

    # print("is the logic same:",constraint_n==constraint)

    # constraint_poly=represent_as_poly(constraint)

    # initail_poly=constraint_poly * (x- D[-4])

    # print("initial_poly:",initail_poly)
    # e1=initail_poly.subs(x,D[12]) %S_PRIME
    # print("subs:",e1)

    factor= [-D[-4],1] # (x- D[-4])
    c1_x= poly_multiply( constraint, factor,S_PRIME)
    this_poly=represent_as_poly(c1_x)
    # print("other poly:", this_poly)
    e2=this_poly.subs(x,D[12]) % S_PRIME
    # print("subs",e2)
    # print(e1==e2)
    return c1_x


# check for inner product poly
c1x=inner_product_contraint_poly(acc_ip_I,b_v_I,s_v_I)
# print("c1_x:", c1x)
print("C1X:", len(c1x))


def conditional_additon_constraint_poly(acc_x,acc_y,b_x,p_x,p_y):

    one_m_bx=poly_subtract([1], b_x, S_PRIME)
    accx_wx =[ acc_x[i]*(omega**i)% S_PRIME for i in range(len(acc_x))] #[ i *omega% S_PRIME for i in acc_x]
    accy_wx = [acc_y[i]* (omega**i)% S_PRIME for i in range(len(acc_y))] #[i * omega% S_PRIME for i in acc_y]
    accx_m_px=poly_subtract(acc_x,p_x,S_PRIME)
    accx_m_px_square=poly_multiply(accx_m_px,accx_m_px,S_PRIME)
    py_x_m_accy_x=poly_subtract(p_y,acc_y,S_PRIME)
    py_x_m_accy_x_square = poly_multiply(py_x_m_accy_x,py_x_m_accy_x,S_PRIME)
    accx_wx_m_accx_x=poly_subtract(accx_wx,acc_x,S_PRIME)
    factor= [-D[-4],1]

    c2_x= poly_add(poly_multiply(b_x,(poly_subtract(poly_multiply(accx_m_px_square,poly_add(poly_add(acc_x,p_x,S_PRIME),accx_wx ,S_PRIME),S_PRIME),py_x_m_accy_x_square,S_PRIME)),S_PRIME)
        ,poly_multiply(one_m_bx, accx_wx_m_accx_x,S_PRIME),S_PRIME)


    c2x=poly_multiply(c2_x,factor,S_PRIME)

    c3_x= poly_add(
        poly_multiply(b_x,poly_subtract(poly_multiply(accx_m_px, poly_add(accy_wx,acc_y,S_PRIME),S_PRIME),poly_multiply(py_x_m_accy_x,accx_wx_m_accx_x,S_PRIME),S_PRIME),S_PRIME),
           poly_multiply(one_m_bx, accx_wx_m_accx_x,S_PRIME),S_PRIME
           )

    c3x= poly_multiply(c3_x,factor,S_PRIME)
    return c2x,c3x

# #check
c2x,c3x=conditional_additon_constraint_poly(acc_x_I,acc_y_I,b_v_I,px_I,py_I)
print("C2X:",len(c2x))
print("C3X:", len(c3x))
# print("constraint 2:", c2x)
# print("constraint 3:",c3x)
def booleanity_constraint_poly(b_x):
    """
    input: bits vector
    output: booleanity constraint
    """
    one_m_bx=poly_subtract( [1],b_x, S_PRIME)
    c4x= poly_multiply(b_x, one_m_bx, S_PRIME)
    return c4x

# check booleanity constraint
c4x=booleanity_constraint_poly(b_v_I)
print("C4X:", len(c4x))

# print("booleanity_constriant-c4x:", c4x)
# print(represent_as_poly(c4x).subs(x,D[509])%S_PRIME)

L_0_x = lagrange_basis_polynomial(D, 0)
L_N_4_x = lagrange_basis_polynomial(D, SIZE - 4)

def conditional_additon_boundary_poly(acc_x,acc_y,S_P, ResultPoint, Result_plus_Seed):

    seed_x,seed_y= S_P
    # print("seed x,y;",seed_x,seed_y)
    # r_x,r_y=ResultPoint
    # print("result",ResultPoint)
    rx_p_sx,ry_p_sy=Result_plus_Seed

    # c5_x=(acc_x -sx) * L_0_x +(acc_x-rx-sx) * L_x_m_4
    c5_x=poly_add( poly_multiply
                   (poly_subtract
                    (acc_x , [seed_x], S_PRIME), L_0_x,S_PRIME),
                   poly_multiply(
                       poly_subtract
                                 (acc_x, [rx_p_sx],S_PRIME),L_N_4_x, S_PRIME), S_PRIME)

    # c6_x=(acc_y -sy)*L_0_x + (acc_y-ry-sy) * L_x_m_4
    c6_x= poly_add(poly_multiply
                   (poly_subtract
                    (acc_y,[seed_y],S_PRIME),L_0_x,S_PRIME),
                   poly_multiply(
                       poly_subtract(acc_y,[ry_p_sy],S_PRIME),L_N_4_x,S_PRIME),S_PRIME)


    return c5_x, c6_x


S_P=twisted_edward_to_sw(SeedPoint)
c5x,c6x= conditional_additon_boundary_poly(acc_x_I,acc_y_I,S_P,Result_point,Result_plus_Seed)
print("C5X, C6X:", len(c5x), len(c6x))
# print("constraint c5x:",c5x)
# print("constraint c6x:",c6x)



def inner_product_boundary_constraint_poly(acc_ip):

    # c7_x=acc_ip *L_0_x + (acc_ip-1)* L_x_m_4
    c7_x=poly_add(poly_multiply(acc_ip, L_0_x, S_PRIME),
                  poly_multiply(poly_subtract(acc_ip,[1],S_PRIME),
                                L_N_4_x,S_PRIME),S_PRIME)

    # c7_x_n = poly_add(poly_multiply(acc_ip, L_0_x, S_PRIME),
    #                 poly_multiply(poly_subtract(acc_ip, [1], S_PRIME),
    #                              L_N_4_x, S_PRIME), S_PRIME)
    # print(c7_x_n==c7_x)
    return c7_x


# check
c7x= inner_product_boundary_constraint_poly(acc_ip_I)
# print("inner_product_contraint c7x:",c7x)
print("C7X:", len(c7x))
end_time=time.time()
print('total_time:',end_time-start_time)
#
#
# cs=[c1x,c2x,c3x,c4x,c5x,c6x,c7x]
# count=0
# for i in cs:
#     print(len(i))
#     evaluations=fft(i,omega,S_PRIME)
#     print(evaluations)
#     print('zeros',evaluations.count(0))
