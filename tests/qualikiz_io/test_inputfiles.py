from subprocess import PIPE, Popen as popen
import unittest
from unittest import TestCase, skip
import copy
import os

from qualikiz_tools.qualikiz_io.inputfiles import *


class TestParticles(TestCase):
    def setUp(self):
        part = {'T': 8.,
                 'n': .1,
                 'At': 5.,
                 'An': 5.,
                 'type': 1,
                 'anis': 1.,
                 'danisdr': 0.}

        ion_0 = copy.deepcopy(part)
        ion_0['n'] = .9
        ion_0['A'] = 2.
        ion_0['Z'] = 1.
        ion_0['type'] = 1
        ion_1 = copy.deepcopy(part)
        ion_1['A'] = 12.
        ion_1['Z'] = 6.
        ion_1['type'] = 2
        ion_2 = copy.deepcopy(part)
        ion_2['A'] = 9.
        ion_2['Z'] = 4.
        ion_2['type'] = 3
        self.ions = IonList(ion_0, ion_1)
        self.ions.append(Ion(**ion_2))
        self.elec = Electron(**part)

    def test_set_ionlist(self):
        value = 10
        self.ions['At'] = value
        for ion in self.ions:
            self.assertEqual(ion['At'], value)

class TestMeta(TestCase):
    meta = {
        'phys_meth': 2,
        'coll_flag': True,
        'rot_flag':  False,
        'verbose':   True,
        'separateflux':   False,
        'numsols':   3,
        'relacc1':   1e-3,
        'relacc2':   2e-2,
        'maxruns':   1,
        'maxpts':    5e5,
        'timeout':   60,
        'R0':        5
    }
    def SetUp(TestCase):
        Meta(meta)

    def test_initialization(self):
        pass

class TestSpecial(TestCase):
    kthetarhos = [0.1, 2.2, 4.4, 6.6, 8.8, 11., 13.2, 15.4,
                  17.6, 19.8, 22., 24.2, 26.4, 28.6, 30.8, 33.]
    def SetUp(TestCase):
        Special(kthetarhos)
    def test_initialization(self):
        pass

class TestGeometric(TestCase):
    geometric = {'x': 0.45,
                 'rho': 0.45,
                 'Ro': 3,
                 'Rmin': 1,
                 'Bo':3,
                 'q':3.,
                 'smag':2.,
                 'alpha':0.,
                 'gammaE': 0.,
                 'Machpar': 0.,
                 'Machtor': 0.,
                 'Aupar': 0.,
                 'Autor':0.,
                 }
    def SetUp(TestCase):
        Geometric(**geometric)
    def test_initialization(self):
        pass

class TestQuaLiKizXpoint(TestCase):
    def setUp(self):
        TestParticles.setUp(self)
        defaults = {}
        defaults.update(TestMeta.meta)
        defaults.update(TestGeometric.geometric)
        options = {
                'set_qn_normni': False,
                'set_qn_normni_ion': 0,
                'set_qn_An': False,
                'set_qn_An_ion': 0,
                'check_qn': False,
                'x_eq_rho': False,
                'recalc_Nustar': False,
                'recalc_Ti_Te_rel': False,
                'assume_tor_rot': False,
                'recalc_Nustar': False,
                'recalc_Ti_Te_rel': False,
                'assume_tor_rot': False
        }
        defaults.update(options)
        self.baseXpoint = QuaLiKizXpoint(TestSpecial.kthetarhos,
                                         self.elec, self.ions, **defaults)

    def test_initialize(self):
        pass

    def test_set_qn_normni_ion_n(self):
        self.baseXpoint['options']['set_qn_normni'] = True
        self.baseXpoint['options']['set_qn_normni_ion'] = 0

        self.baseXpoint['ions'][0]['Z'] = 2
        self.baseXpoint['ions'][1]['Z'] = 6
        self.baseXpoint['ions'][2]['Z'] = 4
        n0s = [0.05, 0.2, 0.365, 0.497]
        n1s = [0.15, 0.1, 0.045, 0.001]
        print('test set_qn')
        for n0, n1 in zip(n0s, n1s):
            self.baseXpoint['ions'][0]['n'] = 0.
            self.baseXpoint['ions'][1]['n'] = n1
            self.baseXpoint.set_qn_normni_ion_n()
            self.assertAlmostEqual(self.baseXpoint['ions'][0]['n'], n0)

        self.baseXpoint['ions'][2]['type'] = 1
        for n0, n1 in zip(n0s, n1s):
            self.baseXpoint['ions'][0]['n'] = 0.
            self.baseXpoint['ions'][1]['n'] = n1/3
            self.baseXpoint['ions'][2]['n'] = n1
            self.baseXpoint.set_qn_normni_ion_n()
            self.assertAlmostEqual(self.baseXpoint['ions'][0]['n'], n0)

    def test_set_qn_An_ion_n_sanity(self):
        self.baseXpoint['options']['set_qn_normni'] = True
        self.baseXpoint['options']['set_qn_normni_ion'] = 0

        self.baseXpoint['ions'][1]['n'] = .9
        self.baseXpoint.set_qn_An_ion_n()
        self.assertRaisesRegex(Exception,
                               'Quasineutrality results in*',
                               self.baseXpoint.set_qn_An_ion_n())


    def test_set_qn_An_ion_n(self):
        self.baseXpoint['options']['set_qn_An'] = True
        self.baseXpoint['options']['set_qn_An_ion'] = 0

        self.baseXpoint['ions'][0]['Z'] = 2
        An0s = [(5-0.09)/1.8, (5-0.06)/1.8,
                (5-0.027)/1.8, (5-0.0006)/1.8]
        An1s = [0.15, 0.1, 0.045, 0.001]
        for An0, An1 in zip(An0s, An1s):
            self.baseXpoint['ions'][0]['An'] = 0.
            self.baseXpoint['ions'][1]['An'] = An1
            self.baseXpoint.set_qn_An_ion_n()
            self.assertAlmostEqual(self.baseXpoint['ions'][0]['An'], An0)

        self.baseXpoint['ions'][2]['type'] = 1
        for An0, An1 in zip(An0s, An1s):
            self.baseXpoint['ions'][0]['An'] = 0.
            self.baseXpoint['ions'][1]['An'] = An1/3
            self.baseXpoint['ions'][2]['An'] = 3*An1/3
            self.baseXpoint.set_qn_An_ion_n()
            self.assertAlmostEqual(self.baseXpoint['ions'][0]['An'], An0)

    def test_check_quasi(self):
        self.baseXpoint['options']['check_qn'] = True
        self.assertRaisesRegex(Exception,
                               'Quasineutrality violated!',
                               self.baseXpoint.check_quasi)
        self.baseXpoint['ions'][0]['n'] = 0.4
        self.baseXpoint.check_quasi()
        self.baseXpoint['ions'][1]['An'] = 4.
        self.assertRaisesRegex(Exception,
                               'Quasineutrality gradient violated!',
                               self.baseXpoint.check_quasi)
        self.baseXpoint['ions'][1]['An'] = 5.
        self.baseXpoint.check_quasi()

    def test_setitem_singles(self):
        test_params = ['Te', 'Ti1', 'ne', 'ni1', 
                       'Ate', 'Ati1', 'Ane', 'Ani1',
                       'typee', 'typei1',
                       'anise','anisi1',
                       'danisdre', 'danisdri1',
                       'Ai1', 'Zi1']
        test_params += (list(QuaLiKizXpoint.Meta.in_args.keys()) +
                        QuaLiKizXpoint.Geometry.in_args +
                        list(QuaLiKizXpoint.Options.in_args.keys()))

        for param in test_params:
            self.baseXpoint[param] = 50
            self.assertEqual(self.baseXpoint[param], 50, param)
            self.setUp()

        self.assertRaisesRegex(NotImplementedError,
                               'setting of*',
                               self.baseXpoint.__setitem__,
                               'made up',
                               50)
        self.assertRaisesRegex(NotImplementedError,
                               'getting of*',
                               self.baseXpoint.__getitem__,
                               'made up')
        self.assertRaisesRegex(NotImplementedError,
                               'getting of*',
                               self.baseXpoint.__getitem__,
                               'made up')
        self.baseXpoint['options']['set_qn_normni'] = True
        self.baseXpoint.__setitem__('ni2', 5)
        self.baseXpoint['options']['set_qn_An'] = True
        self.baseXpoint.__setitem__('ni2', 5)
        self.baseXpoint['options']['check_qn'] = True
        self.baseXpoint.__setitem__('ni2', 5)

    def test_setitem_arrays(self):
        test_params = ['Ti', 'ni', 
                       'Ati', 'Ani',
                       'typei',
                       'anisi',
                       'danisdri',
                       'Ai', 'Zi']
        for param in test_params:
            self.baseXpoint[param] = 50
            self.assertEqual(self.baseXpoint[param], 50,
                             param)

        self.assertRaisesRegex(NotImplementedError,
                               'getting of*',
                               self.baseXpoint['ions'].__getitem__,
                               'made up')

    def test_setitem_kthetarhos(self):
        self.baseXpoint['kthetarhos'] = [1,4,8]
        self.assertEqual(self.baseXpoint['kthetarhos'], [1,4,8])

    def test_getitem_kthetarhos(self):
        self.baseXpoint['kthetarhos']

    def test_setitem_unknown(self):
        with self.assertRaises(NotImplementedError):
            self.baseXpoint['testi'] = 5

    def test_match_zeff(self):
        self.baseXpoint.match_zeff(1.3)
        self.assertAlmostEqual(self.baseXpoint['ions'][0]['n'], .94)
        self.assertAlmostEqual(self.baseXpoint['ions'][1]['n'], .01)
        self.assertEqual(self.baseXpoint['ions'][2]['n'], .1)
        self.baseXpoint.match_zeff(1.7)
        self.assertAlmostEqual(self.baseXpoint['ions'][0]['n'], .86)
        self.assertAlmostEqual(self.baseXpoint['ions'][1]['n'], .02333333333333)
        self.assertEqual(self.baseXpoint['ions'][2]['n'], .1)
        self.assertRaisesRegex(Exception,
                                'Zeff= 0.1 results in unphysical*',
                                self.baseXpoint.match_zeff,
                                0.1)

    def test_calc_zeff(self):
        self.baseXpoint.match_zeff(1.3)
        self.assertAlmostEqual(self.baseXpoint.calc_zeff(), 1.3)

    def test_setitems_zeff(self):
        self.baseXpoint['Zeff'] = 1.1
        self.assertAlmostEqual(self.baseXpoint['Zeff'], 1.1)

    def test_match_nustar(self):
        self.assertEqual(self.baseXpoint['elec']['n'], .1)
        self.assertEqual(self.baseXpoint['geometry']['q'], 3.)
        self.assertEqual(self.baseXpoint['geometry']['Ro'], 3)
        self.assertEqual(self.baseXpoint['geometry']['Rmin'], 1)
        self.assertEqual(self.baseXpoint['geometry']['x'], .45)

        self.baseXpoint.match_nustar(0.1)
        self.assertAlmostEqual(self.baseXpoint['elec']['T'], 0.91676417086826256)

    def test_calc_nustar(self):
        self.assertEqual(self.baseXpoint['elec']['n'], .1)
        self.assertEqual(self.baseXpoint['geometry']['q'], 3.)
        self.assertEqual(self.baseXpoint['geometry']['Ro'], 3)
        self.assertEqual(self.baseXpoint['geometry']['Rmin'], 1)
        self.assertEqual(self.baseXpoint['geometry']['x'], .45)

        self.baseXpoint.match_nustar(0.1)
        self.assertAlmostEqual(self.baseXpoint.calc_nustar(), 0.1)

    def test_setitems_nustar(self):
        self.assertEqual(self.baseXpoint['elec']['n'], .1)
        self.assertEqual(self.baseXpoint['geometry']['q'], 3.)
        self.assertEqual(self.baseXpoint['geometry']['Ro'], 3)
        self.assertEqual(self.baseXpoint['geometry']['Rmin'], 1)
        self.assertEqual(self.baseXpoint['geometry']['x'], .45)

        self.baseXpoint['Nustar'] = 0.1
        self.assertAlmostEqual(self.baseXpoint['Nustar'], 0.1)
        self.assertAlmostEqual(self.baseXpoint['elec']['T'], 0.91676417086826256)

    def test_match_tite(self):
        self.assertEqual(self.baseXpoint['elec']['T'], 8.)
        self.baseXpoint.match_tite(0.1)

        self.assertEqual(self.baseXpoint['ions'][0]['T'], .8)
        self.assertEqual(self.baseXpoint['ions'][1]['T'], .8)
        self.assertEqual(self.baseXpoint['ions'][2]['T'], .8)

    def test_calc_tite(self):
        TiTe = self.baseXpoint.calc_tite()
        self.baseXpoint['ions'][0]['T'] = 5
        self.assertRaisesRegex(Exception,
                                'Ions have non-equal temperatures',
                                self.baseXpoint.calc_tite)

    def test_setitem_tite(self):
        self.assertEqual(self.baseXpoint['elec']['T'], 8.)
        self.baseXpoint['Ti_Te_rel'] = 0.1

        self.assertEqual(self.baseXpoint['ions'][0]['T'], .8)
        self.assertEqual(self.baseXpoint['ions'][1]['T'], .8)
        self.assertEqual(self.baseXpoint['ions'][2]['T'], .8)

    def test_getitem_tite(self):
        self.assertEqual(self.baseXpoint['elec']['T'], 8.)
        self.assertEqual(self.baseXpoint['ions']['T'], 8.)

        self.assertEqual(self.baseXpoint['Ti_Te_rel'], 1)

    @skip('Removed from mainline for now')
    def test_equalize_gradient(self):
        self.baseXpoint['ions']['An'] = 12.
        self.baseXpoint['elec']['An'] = 8.
        self.baseXpoint.equalize_gradient()
        self.assertEqual(self.baseXpoint['ions']['An'], 8)

    def test_match_epsilon(self):
        self.baseXpoint['geometry']['Rmin'] = 2.
        self.assertEqual(self.baseXpoint['geometry']['Ro'], 3.)
        self.assertEqual(self.baseXpoint['geometry']['Rmin'], 2.)

        self.baseXpoint.match_epsilon(.5)
        self.assertEqual(self.baseXpoint['geometry']['x'], 0.75)

    def test_setitem_epsilon(self):
        self.baseXpoint['geometry']['Rmin'] = 2.
        self.assertEqual(self.baseXpoint['geometry']['Ro'], 3.)
        self.assertEqual(self.baseXpoint['geometry']['Rmin'], 2.)

        self.baseXpoint['epsilon'] = .5
        self.assertEqual(self.baseXpoint['geometry']['x'], 0.75)

    def test_calc_epsilon(self):
        self.assertEqual(self.baseXpoint['geometry']['Ro'], 3.)
        self.assertEqual(self.baseXpoint['geometry']['Rmin'], 1.)
        self.assertEqual(self.baseXpoint['geometry']['x'], 0.45)

        self.assertEqual(self.baseXpoint.calc_epsilon(), 0.15)

    def test_getitem_epsilon(self):
        self.assertEqual(self.baseXpoint['geometry']['Ro'], 3.)
        self.assertEqual(self.baseXpoint['geometry']['Rmin'], 1.)
        self.assertEqual(self.baseXpoint['geometry']['x'], 0.45)

        self.assertEqual(self.baseXpoint['epsilon'], 0.15)

class TestQuaLiKizPlan_hyperedge(TestCase):
    def setUp(self):
        TestQuaLiKizXpoint.setUp(self)
        scan_dict = OrderedDict()
        keys = ['Ati', 'Ate', 'Ane', 'q', 'smag', 'x', 'Ti_Te_rel', 'Zeff']
        values = [
            np.linspace(0,1,1),
            np.linspace(0,1,2),
            np.linspace(0,1,3),
            np.linspace(0,1,4),
            np.linspace(0,1,5),
            np.linspace(0,1,6),
            np.linspace(0,1,7),
            np.linspace(1,3,8)
                  ]
        for key, value in zip(keys, values):
            scan_dict[key] = value.tolist()
        self.qualikizplan = QuaLiKizPlan(scan_dict, 'hyperedge', self.baseXpoint)

    def test_initialize(self):
        kthetarhos = self.qualikizplan['xpoint_base']['special']['kthetarhos']
        self.assertEqual(len(kthetarhos), 16)

    def test_calculate_dimx(self):
        self.assertEqual(self.qualikizplan.calculate_dimx(), 36)

    def test_calculate_dimxn(self):
        self.assertEqual(self.qualikizplan.calculate_dimxn(), 576)

    def test_unknown_plan(self):
        self.qualikizplan['scan_type'] = 'test'
        with self.assertRaisesRegex(Exception, 'Unknown scan_type*'):
            self.qualikizplan.setup()
        with self.assertRaisesRegex(Exception, 'Unknown scan_type*'):
            self.qualikizplan.calculate_dimx()

    def test_setup(self):
        scan_dict = OrderedDict([('Ati', [0, 2, 4]),
                                 ('Ate', [1, 3, 5]),
                                 ('Ane', [6, 9, 12])])
        self.qualikizplan['scan_dict'] = scan_dict
        byte_arrays = self.qualikizplan.setup()
        self.assertEqual(byte_arrays['Ati'],
                         array.array('d', [0, 2, 4, 0, 0, 0, 0, 0, 0,
                                           0, 2, 4, 0, 0, 0, 0, 0, 0,
                                           0, 2, 4, 0, 0, 0, 0, 0, 0]))
        self.assertEqual(byte_arrays['Ate'],
                         array.array('d', [1, 1, 1, 1, 3, 5, 1, 1, 1]))
        self.assertEqual(byte_arrays['Ane'],
                         array.array('d', [6, 6, 6, 6, 6, 6, 6, 9, 12]))

class TestQuaLiKizPlan_hyperedge_files(TestCase):
    def setUp(self):
        TestQuaLiKizPlan_hyperedge.setUp(self)

    def test_to_json(self):
        self.qualikizplan.to_json('test.json')

    def test_from_json(self):
        self.qualikizplan.to_json('test.json')
        newplan = QuaLiKizPlan.from_json('test.json')
        self.assertEqual(self.qualikizplan, newplan)

    def tearDown(self):
        try:
            os.remove('test.json')
        except FileNotFoundError:
            pass

class TestQuaLiKizPlan_hyperrect(TestCase):
    def setUp(self):
        TestQuaLiKizPlan_hyperedge.setUp(self)
        self.qualikizplan['scan_type'] = 'hyperrect'

    def test_initialize(self):
        kthetarhos = self.qualikizplan['xpoint_base']['special']['kthetarhos']
        self.assertEqual(len(kthetarhos), 16)

    def test_calculate_dimx(self):
        self.assertEqual(self.qualikizplan.calculate_dimx(), 40320)

    def test_calculate_dimxn(self):
        self.assertEqual(self.qualikizplan.calculate_dimxn(), 645120)

    def test_setup(self):
        scan_dict = OrderedDict([('Ati', [0, 2, 4]),
                                 ('Ate', [1, 3, 5]),
                                 ('Ane', [6, 9, 12])])
        self.qualikizplan['scan_dict'] = scan_dict
        byte_arrays = self.qualikizplan.setup()
        self.assertEqual(byte_arrays['Ati'],
                         array.array('d', [0, 0, 0, 0, 0, 0, 0, 0, 0,
                                           2, 2, 2, 2, 2, 2, 2, 2, 2,
                                           4, 4, 4, 4, 4, 4, 4, 4, 4,
                                           0, 0, 0, 0, 0, 0, 0, 0, 0,
                                           2, 2, 2, 2, 2, 2, 2, 2, 2,
                                           4, 4, 4, 4, 4, 4, 4, 4, 4,
                                           0, 0, 0, 0, 0, 0, 0, 0, 0,
                                           2, 2, 2, 2, 2, 2, 2, 2, 2,
                                           4, 4, 4, 4, 4, 4, 4, 4, 4]))
        self.assertEqual(byte_arrays['Ate'],
                         array.array('d', [1, 1, 1, 3, 3, 3, 5, 5, 5,
                                           1, 1, 1, 3, 3, 3, 5, 5, 5,
                                           1, 1, 1, 3, 3, 3, 5, 5, 5]))
        self.assertEqual(byte_arrays['Ane'],
                         array.array('d', [6, 9, 12, 6, 9, 12, 6, 9, 12,
                                           6, 9, 12, 6, 9, 12, 6, 9, 12,
                                           6, 9, 12, 6, 9, 12, 6, 9, 12]))

class TestQuaLiKizPlan_hyperrect_files(TestCase):
    def setUp(self):
        TestQuaLiKizPlan_hyperrect.setUp(self)

    def test_to_json(self):
        self.qualikizplan.to_json('test.json')

    def test_from_json(self):
        self.qualikizplan.to_json('test.json')
        newplan = QuaLiKizPlan.from_json('test.json')
        self.assertEqual(self.qualikizplan, newplan)

    def tearDown(self):
        try:
            os.remove('test.json')
        except FileNotFoundError:
            pass
