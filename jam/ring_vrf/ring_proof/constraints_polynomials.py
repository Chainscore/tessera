from jam.ring_vrf.ring_proof.constants import S_PRIME, SeedPoint
from jam.ring_vrf.ring_proof.preprocessing import px_I, py_I, s_v_I, D, Result_point, size
from jam.ring_vrf.ring_proof.prover_witness_polynomials import acc_x_I,acc_y_I,acc_ip_I,b_v_I
from sympy import symbols, expand,simplify
from jam.ring_vrf.ring_proof.short_weierstrass import short_to_te

x, omega_x, N_m4= symbols('x omega_x N_m4')


def inner_product_contraint_poly(accip_x,b_x,s_x):
    # Define symbols

    accip_omega_x=accip_x.subs(x,omega_x)

    #Compute constraint polynomial
    constraint = (accip_omega_x - accip_x- b_x*s_x ) *(x- N_m4)
    # print(constraint)
    #Expand the polynomial
    c1_x = expand(constraint) % S_PRIME
    return c1_x

#check for inner product poly
c1x=inner_product_contraint_poly(acc_x_I,b_v_I,s_v_I)
idx=1
substitutions = {x: D[idx], omega_x: D[idx+1], N_m4: D[-5]}
final_result = c1x.subs(substitutions)
print("Inner Product Constraint C1X:", final_result)


def conditional_additon_constraint_poly(acc_x,acc_y,b_x,p_x,p_y):

    acc_x_1 = acc_x.subs(x, omega_x)
    acc_y_1 = acc_x.subs(x, omega_x)
    c2_x = (b_x * ((acc_x - p_x) ** 2 * (acc_x + p_x + acc_x_1)-
                     ((p_y - acc_y) ** 2)) +
            (1 - b_x) * (acc_x_1 - acc_x)) * (x - N_m4)

    c2_x=expand(c2_x)

    c3_x = (b_x * ((acc_x - p_x) * (acc_y_1 + acc_y) -
                     (p_y - acc_y) * (acc_x_1 - acc_x)) +
            (1 - b_x) * (acc_x_1 - acc_x)) * (x - N_m4)

    c3_x=expand(c3_x)

    return c2_x % S_PRIME, c3_x % S_PRIME

#check
c2x,c3x=conditional_additon_constraint_poly(acc_x_I,acc_y_I,b_v_I,px_I,py_I)
idx=1
substitutions = {x: D[idx], omega_x: D[idx+1], N_m4: D[-5]}
final_result_c3x = c3x.subs(substitutions)
final_result_c2x=c2x.subs(substitutions)
print("Conditional Addition Constraint C2X:", final_result_c2x)
print("Conditional Addition Constraint C3X:", final_result_c3x)


def booleanity_constraint_poly(b_x):

    c4x=b_x * (1-b_x)
    c4_x=expand(c4x)
    return c4_x % S_PRIME


# check booleanity constraint
c4x=booleanity_constraint_poly(b_v_I)
idx=3
solution=c4x.subs(x,D[idx])
print("Booleanity constraint C4X:",solution)



def lagrange_D_poly(i, D):
    """
    """
    # Define symbolic variable x
    x_i = D[i]  # Reference point x_i
    L_i = 1  # Initialize polynomial

    # Compute the Lagrange basis polynomial L_i(x)
    for j in range(len(D)):
        if j != i:
            x_j = D[j]
            L_i *= (x - x_j) / (x_i - x_j)

    return simplify(L_i)



def conditional_additon_boundary_poly(acc_x,acc_y,SeedPoint,Result_point,idx=0):
    sx, sy = SeedPoint
    rx, ry = Result_point
    if idx==size-4:
        print("in me")
        L_0_x = 0
        L_x_m_4 = 1

    elif idx==0:
        L_0_x=1
        L_x_m_4=0

    else:
        L_0_x=lagrange_D_poly(idx,D)
        L_x_m_4=lagrange_D_poly(idx-4,D)

    c5_x=(acc_x -sx) * L_0_x +(acc_x-rx-sx) * L_x_m_4

    c6_x=(acc_y -sy)*L_0_x + (acc_y-ry-sy) * L_x_m_4

    c5_x=expand(c5_x)
    c6_x=expand(c6_x)
    return c5_x % S_PRIME, c6_x % S_PRIME

#check
SeedPoint=short_to_te(SeedPoint)
idx= 0 #6
c5x,c6x= conditional_additon_boundary_poly(acc_x_I,acc_y_I,SeedPoint,Result_point,idx)
substitutions = {x: D[idx], omega_x: D[idx+1], N_m4: D[-5]}
c6x_result=c6x.subs(substitutions)
c5x_result=c5x.subs(substitutions)
print("C5x Evaluation:",c5x_result)
print("C6X Evaluation:",c6x_result)


def inner_product_boundary_constraint_poly(acc_ip,idx=0):

    if idx==size-4:
        L_0_x = 0
        L_x_m_4 = 1

    elif idx==0:
        L_0_x=1
        L_x_m_4=0
    else:
        L_0_x=lagrange_D_poly(idx,D)
        L_x_m_4=lagrange_D_poly(idx-4,D)
    c7_x=acc_ip *L_0_x + (acc_ip-1)* L_x_m_4
    c7_x=expand(c7_x)
    return c7_x % S_PRIME

#check for ipbcp
idx=6 #0
c7x= inner_product_boundary_constraint_poly(acc_ip_I,idx)
substitutions = {x: D[idx], omega_x: D[idx+1], N_m4: D[-5]}
c7x_result=c7x.subs(substitutions)
print("C7x_Result:",c7x_result)

constraints=[c1x,c2x,c3x,c4x,c5x,c6x,c7x]
for constraint in constraints:
    print(constraint)
