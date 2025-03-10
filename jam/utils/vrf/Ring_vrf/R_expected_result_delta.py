from sympy.crypto import bg_public_key


def compute_conditional_sum(b, public_keys, S, p):
    Rx, Ry = S  # Initialize with the seeding point

    for i in range(len(public_keys)):
        if b[i] == 1:
            Px, Py = public_keys[i]
            Rx = (Rx + Px) % p
            Ry = (Ry + Py) % p

    return Rx, Ry


# # Example values
# bit_vector = [1, 0, 1]  # Example bit selection
# public_keys = [(100, 200), (300, 400), (500, 600)]
# S = (10, 20)  # Seeding point
#
# R = compute_conditional_sum(bit_vector, public_keys, S)
# print("R_x, R_y:", R)
