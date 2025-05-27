import time
import random
import pytest
import numpy as np
from sympy import symbols

from numpy.polynomial.polynomial import Polynomial
# from jam.ring_vrf.ring_proof.constants import D, S_PRIME
# from jam.ring_vrf.ring_proof.polynomial_interpolation import polynomial_interpolation
# from scipy.interpolate import lagrange
# import matplotlib.pyplot as plt
# from jam.ring_vrf.ring_proof.preprocessing import s_vector

# random.seed(10)

# def selector_vector(size=512):
#     """
#     input: ring of public key's
#     output: selecting vector having 0/1
#     """
#     s_vector = []
#     N_K=255
#
#     for i in range(size):
#         if i<N_K:
#             s_vector.append(1)
#         else:
#             s_vector.append(0)
#
#     return s_vector

# def test_scipy_interpolation_timing():
#     """Test the performance of scipy's interpolation function."""
#     sizes = [10, 50]
#     times = []
    
#     for size in sizes:
#         # Generate random points
#         x_coords = np.array(D)
#         y_coords = np.array(selector_vector())
        
#         # Time the interpolation
#         start_time = time.time()    
#         interp = lagrange(x_coords, y_coords)
#         print([val for val in interp.c])
#         end_time = time.time()
        
#         # Record the time
#         elapsed = end_time - start_time
#         times.append(elapsed)
#         print(f"Size {size}: {elapsed:.6f} seconds")
#         # Plot the polynomial
#         plt.scatter(x_coords, y_coords, label='data')
#         plt.plot(x_coords, Polynomial(interp.c[::-1])(x_coords), label='Polynomial')
#         plt.plot(x_coords, 3*x_coords**2 - 2*x_coords + 0*x_coords, linestyle='--')
#         plt.legend()
#         plt.show()

# def test_scipy_interpolation_timing():
#     """Test the performance of scipy's interpolation function."""

#     x_coords = np.array(D)
#     y_coords = np.array(selector_vector())
    
#     # Time the interpolation
#     start_time = time.time()    
#     interp = lagrange(x_coords, y_coords)
#     print([val for val in interp.c])
#     end_time = time.time()
    
#     # Record the time
#     elapsed = end_time - start_time
#     print(f"Time taken: {elapsed:.6f} seconds")
#     # Plot the polynomial
#     plt.scatter(x_coords, y_coords, label='data')
#     plt.plot(x_coords, Polynomial(interp.c[::-1])(x_coords), label='Polynomial')
#     plt.plot(x_coords, 3*x_coords**2 - 2*x_coords + 0*x_coords, linestyle='--')
#     plt.legend()
#     plt.show()


# def test_scipy_example():
#     import numpy as np
#     from scipy.interpolate import lagrange
#     x = np.array([0, 1, 2])
#     y = x**3
#     poly = lagrange(x, y)
#     print(poly.c)

#     from numpy.polynomial.polynomial import Polynomial
#     Polynomial(poly.coef[::-1]).coef

#     import matplotlib.pyplot as plt
#     x_new = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
#     plt.scatter(x, y, label='data')
#     plt.plot(x_new, Polynomial(poly.coef[::-1])(x_new), label='Polynomial')
#     # plt.plot(x_new, 3*x_new**2 - 2*x_new + 0*x_new,
#     #         label=r"$3 x^2 - 2 x$", linestyle='-.')
#     plt.legend()
#     plt.show()
    

# def test_polynomial_interpolation_correctness():
#     """Test that the interpolated polynomial passes through all input points."""
#     # Create test data
#     x_coords = [3, 7, 13, 21, 42]
#     y_coords = [2, 10, 5, 8, 15]
    
#     # Perform interpolation
#     poly = polynomial_interpolation(x_coords, y_coords)
#     check_is_valid(poly, x_coords, y_coords)
    
#     # Verify that the polynomial passes through all points
#     x = symbols('x')
#     for i in range(len(x_coords)):
#         assert poly.subs(x, x_coords[i]) % S_PRIME == y_coords[i] % S_PRIME

# @pytest.mark.parametrize("num_points", [10, 50, 100])
# def test_polynomial_interpolation_benchmark(num_points, benchmark):
#     """Benchmark polynomial interpolation with different numbers of points."""
    
#     def setup():
#         # Generate random points in the finite field
#         x_coords = [random.random() * S_PRIME for _ in range(num_points)]
#         y_coords = [random.random() * S_PRIME for _ in range(num_points)]
#         return x_coords, y_coords
    
#     # Run the benchmark
#     benchmark.pedantic(polynomial_interpolation, setup())

# def test_polynomial_interpolation_manual_timing():
#     """Manually time polynomial interpolation with different sizes to see detailed scaling."""
#     sizes = [10, 50]
#     times = []
    
#     for size in sizes:
#         # Generate random points
#         x_coords = [random.randint(0, 1000000) for _ in range(size)]
#         y_coords = [random.randint(0, 1000000) for _ in range(size)]
        
#         # Time the interpolation
#         start_time = time.time()
#         poly = polynomial_interpolation(x_coords, y_coords)
#         print(poly)
#         end_time = time.time()
        
#         # Validate the interpolation
#         # check_is_valid(poly, x_coords, y_coords)
        
#         # Record the time
#         elapsed = end_time - start_time
#         times.append(elapsed)
#         print(f"Size {size}: {elapsed:.6f} seconds")
    
#     # Optional: plot the results if matplotlib is available
#     try:
#         import matplotlib.pyplot as plt
#         plt.figure(figsize=(10, 6))
#         plt.plot(sizes, times, 'o-')
#         plt.xlabel('Number of Points')
#         plt.ylabel('Time (seconds)')
#         plt.title('Polynomial Interpolation Performance')
#         plt.grid(True)
#         plt.savefig('polynomial_interpolation_benchmark.png')
#         print("Performance plot saved to polynomial_interpolation_benchmark.png")
#     except ImportError:
#         print("Matplotlib not available for plotting results")

# def test_interpolation_with_edge_cases():
#     """Test polynomial interpolation with edge cases."""
    
#     # Test with minimum number of points (2)
#     x_coords = [1, 2]
#     y_coords = [5, 7]
#     poly = polynomial_interpolation(x_coords, y_coords)
#     check_is_valid(poly, x_coords, y_coords)
    
#     # Test with sequential x values
#     x_coords = list(range(1, 101))
#     y_coords = [random.random() * S_PRIME for _ in range(100)]
#     start_time = time.time()
#     poly = polynomial_interpolation(x_coords, y_coords)
#     end_time = time.time()
#     print(f"Sequential x values (100 points): {end_time - start_time:.6f} seconds")
    
#     # Test with x values being powers of a small value (similar to domain roots)
#     base = 7
#     x_coords = [pow(base, i, S_PRIME) for i in range(50)]
#     y_coords = [random.random() * S_PRIME for _ in range(50)]
#     start_time = time.time()
#     poly = polynomial_interpolation(x_coords, y_coords)
#     end_time = time.time()
#     print(f"Powers of {base} (50 points): {end_time - start_time:.6f} seconds")