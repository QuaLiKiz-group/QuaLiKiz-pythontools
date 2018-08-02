import numpy as np
import scipy.special.lambertw as lambertw
from warnings import warn

def calc_c1(zeff, ne, q, Ro, Rmin, x):
    c1 = (6.9224e-5 * zeff * ne *q * Ro * (Rmin * x / Ro) ** -1.5)
    return c1

def calc_c2(ne):
    c2 = 15.2 - 0.5 * np.log(0.1 * ne)
    return c2

def calc_te_from_nustar(zeff, ne, nustar, q, Ro, Rmin, x):
    c1 = calc_c1(zeff, ne, q, Ro, Rmin, x)
    c2 = calc_c2(ne)

    z = np.array(-2 * np.exp(-2 * c2) * nustar / c1, ndmin=1)
    real_branches = []
    if any(z > - 1/np.e):
        real_branches.append(0)
    if any((-1/np.e < z) & (z < 0)):
        real_branches.append(-1)
    if len(real_branches) == 0:
        raise Exception('No real solution')

    for branch in real_branches:
        sol = (1j * np.sqrt(c1) * np.sqrt(lambertw(z, branch))/
               np.sqrt(2 * nustar))
        sol = sol.real # Solution only has a real part
        # -sol and sol are both solutions, but Te is > 0
        sol[sol < 0] = -sol[sol < 0]
        calced_nustar = calc_nustar_from_c1_c2(c1, c2, sol)
        if all(np.isclose(calced_nustar,
                      nustar)):
            Te = sol
            break

    return Te

def calc_nustar_from_c1_c2(c1, c2, Te):
    nustar = c1 / Te ** 2 * (c2 + np.log(Te))
    return nustar

def calc_nustar_from_parts(zeff, ne, Te, q, Ro, Rmin, x):
    c1 = calc_c1(zeff, ne, q, Ro, Rmin, x)
    c2 = calc_c2(ne)
    nustar = calc_nustar_from_c1_c2(c1, c2, Te)
    return nustar

def calc_zeff(ionlist):
    zeff = sum(ion['n'] * ion['Z'] ** 2 for ion in ionlist)
    return zeff

def calc_puretor_Machpar_from_Machtor(Machtor, epsilon, q):
    if Machtor == 0:
        warn('Machtor is zero! Machpar will be zero too')
    Machpar = Machtor / np.sqrt(1 + (epsilon / q)**2)
    return Machpar

def calc_puretor_Autor_from_gammaE(gammaE, epsilon, q):
    if gammaE == 0:
        warn('gammaE is zero! Autor will be zero too')
    Autor = -gammaE * q / epsilon
    return Autor

def calc_puretor_Aupar_from_Autor(Autor, epsilon, q):
    if Autor == 0:
        warn('Autor is zero! Aupar will be zero too')
    Aupar = Autor / np.sqrt(1 + (epsilon / q)**2)
    return Aupar

def calc_puretor_gammaE_from_Autor(Autor, epsilon, q):
    if Autor == 0:
        warn('Autor is zero! gammaE will be infinte!')
    gammaE = -epsilon / q * Autor
    return gammaE
