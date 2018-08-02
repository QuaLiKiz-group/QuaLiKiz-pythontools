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

class TestPuretor(TestCase):
    def test_calc_puretor_Machpar_from_Machtor(self):
        eps = .28
        q = 0.66
        Machtor = 0.67
        Machpar = calc_puretor_Machpar_from_Machtor(Machtor, eps, q)
        self.assertAlmostEqual(Machpar, 0.616789793856422)

    def test_calc_puretor_Autor_from_gammaE(self):
        eps = .28
        q = 0.66
        gammaE = -0.7
        Autor = calc_puretor_Autor_from_gammaE(gammaE, eps, q)
        self.assertAlmostEqual(Autor, 1.6499999999999997)

    def test_calc_puretor_Aupar_from_Autor(self):
        eps = .28
        q = 0.66
        Autor = 5
        Aupar = calc_puretor_Aupar_from_Autor(Autor, eps, q)
        self.assertAlmostEqual(Aupar, 4.602908909376283)

    def test_calc_puretor_gammaE_from_Autor(self):
        eps = .28
        q = 0.66
        Autor = 5
        gammaE = calc_puretor_gammaE_from_Autor(Autor, eps, q)
        self.assertAlmostEqual(gammaE, -2.121212121212121)

    def test_calc_puretor_absolute_Machtor(self):
        eps = .28
        q = 0.66
        Machtor = 0.67
        [Machtor_calc, Machpar_calc] = calc_puretor_absolute(eps, q, Machtor=Machtor)
        self.assertAlmostEqual(Machpar_calc, 0.616789793856422)
        self.assertEqual(Machtor_calc, Machtor)

    def test_calc_puretor_absolute_none(self):
        eps = .28
        q = 0.66
        self.assertRaises(ValueError, calc_puretor_absolute, eps, q)

    def test_calc_puretor_absolute_two(self):
        eps = .28
        q = 0.66
        Machtor = 0.67
        Machpar = 0.616789793856422
        self.assertRaises(ValueError, calc_puretor_absolute, eps, q, Machtor=Machtor, Machpar=Machpar)

    def test_calc_puretor_gradient_Autor(self):
        eps = .28
        q = 0.66
        Autor = 5
        [Aupar_calc, Autor_calc, gammaE_calc] = calc_puretor_gradient(eps, q, Autor=Autor)
        self.assertAlmostEqual(gammaE_calc, -2.121212121212121)
        self.assertEqual(Autor_calc, Autor)

    def test_calc_puretor_gradient_none(self):
        eps = .28
        q = 0.66
        self.assertRaises(ValueError, calc_puretor_absolute, eps, q)

    def test_calc_puretor_gradient_two(self):
        eps = .28
        q = 0.66
        Autor = 5
        Aupar = 4.602908909376283
        self.assertRaises(ValueError, calc_puretor_gradient, eps, q,  Aupar=Autor, Autor=Autor)

    def test_calc_puretor_gradient_three(self):
        eps = .28
        q = 0.66
        Autor = 5
        Aupar = 4.602908909376283
        gammaE = -2.121212121212121
        self.assertRaises(ValueError, calc_puretor_gradient, eps, q,  Aupar=Autor, Autor=Autor, gammaE=gammaE)
