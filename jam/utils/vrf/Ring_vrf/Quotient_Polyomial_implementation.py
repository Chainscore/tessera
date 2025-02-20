from sympy import symbols,simplify
def quotient_polynomial(c_poly, N):
    x = symbols('x')
    vanishing_poly = x**N - 1
    q_poly = simplify(c_poly / vanishing_poly)
    return q_poly

def main():
    c_poly=16*2**3 + 26*3**2 + 16*4+ 40
    N=2048
    q_poly=quotient_polynomial(c_poly,N)
    print('q_poly=',q_poly)

if __name__=="__main__":
    main()

