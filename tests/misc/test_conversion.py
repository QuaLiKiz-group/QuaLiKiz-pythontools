import unittest
from unittest import TestCase, skip
import copy
import os

from numpy.testing import assert_almost_equal

from qualikiz_tools.misc.conversion import *

class TestZeff(TestCase):
    def test_calc_zeff(self):
        ions = [
            {'n': .94, 'Z': 1},
            {'n': .01, 'Z': 6},
        ]
        zeff = calc_zeff(ions)
        self.assertAlmostEqual(zeff, 1.3)

        ions = [
            {'n': .9, 'Z': 1},
            {'n': .1, 'Z': 6},
        ]
        zeff = calc_zeff(ions)
        self.assertAlmostEqual(zeff, 4.5)

class TestNustar(TestCase):
    def test_calc_c2(self):
        ne = .1
        c2 = calc_c2(ne)
        self.assertAlmostEqual(c2, 17.502585093)

    def test_calc_c1(self):
        ne = .1
        q = 3
        Ro = 3
        Rmin = 1
        x = .45
        zeff = 4.5
        c1 = calc_c1(zeff, ne, q, Ro, Rmin, x)
        self.assertAlmostEqual(c1, 0.00482586118484152)

    def test_calc_nustar_from_c1_c2(self):
        ne = .1
        q = 3
        Ro = 3
        Rmin = 1
        x = .45
        Te = 0.91676417086826256
        zeff = 4.5
        c1 = calc_c1(zeff, ne, q, Ro, Rmin, x)
        c2 = calc_c2(ne)
        nustar_calc = calc_nustar_from_c1_c2(c1, c2, Te)
        self.assertAlmostEqual(nustar_calc, 0.1)

    def test_calc_nustar_from_parts(self):
        ne = .1
        q = 3
        Ro = 3
        Rmin = 1
        x = .45
        Te = 0.91676417086826256
        zeff = 4.5
        nustar_calc = calc_nustar_from_parts(zeff, ne, Te, q, Ro, Rmin, x)
        self.assertAlmostEqual(nustar_calc, 0.1)

        ne = 5
        q = 0.66
        Ro = 3
        Rmin = 1
        x = .33
        Te = 7.48836
        zeff = 1.7
        nustar_calc = calc_nustar_from_parts(zeff, ne, Te, q, Ro, Rmin, x)
        self.assertAlmostEqual(nustar_calc, 1e-2)

    def test_calc_nustar_from_parts_array(self):
        ne   = np.array([.1, 5])
        q    = np.array([3, 0.66])
        Ro   = np.array([3, 3])
        Rmin = np.array([1, 1])
        x    = np.array([.45, .33])
        Te   = np.array([0.91676417086826256, 7.4883686])
        zeff = np.array([4.5, 1.7])
        nustar_calc = calc_nustar_from_parts(zeff, ne, Te, q, Ro, Rmin, x)

    def test_calc_te_from_nustar(self):
        ne = .1
        q = 3
        Ro = 3
        Rmin = 1
        x = .45
        nustar = 0.1
        zeff = 4.5
        te_calc = calc_te_from_nustar(zeff, ne, nustar, q, Ro, Rmin, x)
        assert_almost_equal(te_calc, 0.91676417086826256)

        ne = 5
        q = 0.66
        Ro = 3
        Rmin = 1
        x = .33
        nustar = 0.01
        zeff = 1.7
        te_calc = calc_te_from_nustar(zeff, ne, nustar, q, Ro, Rmin, x)
        assert_almost_equal(te_calc, 7.4883686)

    def test_calc_nustar_from_parts_array(self):
        ne   = np.array([.1, 5])
        q    = np.array([3, 0.66])
        Ro   = np.array([3, 3])
        Rmin = np.array([1, 1])
        x    = np.array([.45, .33])
        nustar = np.array([0.1, 0.01])
        zeff = np.array([4.5, 1.7])
        te_calc = calc_te_from_nustar(zeff, ne, nustar, q, Ro, Rmin, x)
        te   = np.array([0.91676417086826256, 7.4883686])
        assert_almost_equal(te_calc, te)
