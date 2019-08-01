from math import exp, sqrt, pi

cdef float cgaussian(float sigma, float x, float mu):
    if sigma == 0: return 1
    x = (x - mu) / sigma
    return exp(-x*x/2.0) / sqrt(2.0 * pi) / sigma

def gaussian(sigma, x, mu):
    return cgaussian(sigma, x, mu)