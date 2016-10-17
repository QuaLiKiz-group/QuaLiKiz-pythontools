from subprocess import PIPE, Popen as popen
import unittest
from unittest import TestCase
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
        ion_2['A'] = 12.
        ion_2['Z'] = 6.
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
    geometric = {'x': 0.15,
                 'rho': 0.15,
                 'Ro': 3,
                 'Rmin': 1,
                 'Bo':3,
                 'qx':2.,
                 'smag':1.,
                 'alphax':0.,
                 'Machtor': 0.,
                 'Autor':0.}
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
        norm = {'ninorm1': False,
                'Ani1':    False,
                'QN_grad': False,
                'x_rho':   False}
        defaults.update(norm)
        self.baseXpoint = QuaLiKizXpoint(TestSpecial.kthetarhos,
                                         self.elec, self.ions, **defaults)

    def test_initialize(self):
        TestParticles.setUp(self)
        defaults = {}
        defaults.update(TestMeta.meta)
        defaults.update(TestGeometric.geometric)
        norm = {'ninorm1': True,
                'Ani1':    True,
                'QN_grad': True,
                'x_rho':   True}
        defaults.update(norm)
        self.baseXpoint = QuaLiKizXpoint(TestSpecial.kthetarhos,
                                         self.elec, self.ions, **defaults)

    def test_normalize_density(self):
        self.baseXpoint['ninorm'] = True
        self.baseXpoint['ions'][0]['Z'] = 2
        n0s = [0.05, 0.2, 0.365, 0.497]
        n1s = [0.15, 0.1, 0.045, 0.001]
        for n0, n1 in zip(n0s, n1s):
            self.baseXpoint['ions'][0]['n'] = 0.
            self.baseXpoint['ions'][1]['n'] = n1
            self.baseXpoint.normalize_density()
            self.assertAlmostEqual(self.baseXpoint['ions'][0]['n'], n0)
            
        self.baseXpoint['ions'][2]['type'] = 1
        for n0, n1 in zip(n0s, n1s):
            self.baseXpoint['ions'][0]['n'] = 0.
            self.baseXpoint['ions'][1]['n'] = n1/3
            self.baseXpoint['ions'][2]['n'] = 2*n1/3
            self.baseXpoint.normalize_density()
            self.assertAlmostEqual(self.baseXpoint['ions'][0]['n'], n0)
    
    def test_normalize_density_sanity(self):
        self.baseXpoint['ions'][1]['n'] = .9
        self.assertRaisesRegex(Exception,
                               'Quasineutrality results in*',
                               self.baseXpoint.normalize_density)


    def test_normalize_density(self):
        self.baseXpoint['Ani1'] = True
        self.baseXpoint['ions'][0]['Z'] = 2
        An0s = [(5-0.09)/1.8, (5-0.06)/1.8,
                (5-0.027)/1.8, (5-0.0006)/1.8]
        An1s = [0.15, 0.1, 0.045, 0.001]
        for An0, An1 in zip(An0s, An1s):
            self.baseXpoint['ions'][0]['An'] = 0.
            self.baseXpoint['ions'][1]['An'] = An1
            self.baseXpoint.normalize_gradient()
            self.assertAlmostEqual(self.baseXpoint['ions'][0]['An'], An0)
            
        self.baseXpoint['ions'][2]['type'] = 1
        for An0, An1 in zip(An0s, An1s):
            self.baseXpoint['ions'][0]['An'] = 0.
            self.baseXpoint['ions'][1]['An'] = An1/3
            self.baseXpoint['ions'][2]['An'] = 2*An1/3
            self.baseXpoint.normalize_gradient()
            self.assertAlmostEqual(self.baseXpoint['ions'][0]['An'], An0)

    def test_check_quasi(self):
        self.baseXpoint['norm']['QN_grad'] = True
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
        test_params += (QuaLiKizXpoint.Meta.keynames +
                        QuaLiKizXpoint.Geometry.in_args +
                        QuaLiKizXpoint.Geometry.extra_args +
                        ['ninorm1', 'Ani1', 'QN_grad', 'x_rho'])

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
                               'made upi')
        self.baseXpoint['norm']['ninorm1'] = True
        self.baseXpoint.__setitem__('ni2', 5)
        self.baseXpoint['norm']['Ani1'] = True
        self.baseXpoint.__setitem__('ni2', 5)
        self.baseXpoint['norm']['QN_grad'] = True
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
            self.assertEqual(self.baseXpoint[param], [50, 50, 50],
                             param)

        self.assertRaisesRegex(NotImplementedError,
                               'getting of*',
                               self.baseXpoint['ions'].__getitem__,
                               'made up')

    def test_getitem_kthetarhos(self):
        self.baseXpoint['kthetarhos']

    @unittest.expectedFailure
    def test_match_zeff(self):
        self.baseXpoint.match_zeff(1.1)
        self.assertRaisesRegex(Exception,
                                'Given Zeff results in*',
                                self.baseXpoint.match_zeff,
                                0.1)
        raise NotImplementedError('Value check')

    @unittest.expectedFailure
    def test_calc_zeff(self):
        self.baseXpoint.calc_zeff()
        raise NotImplementedError('Value check')

    def test_setitems_zeff(self):
        self.baseXpoint['Zeff'] = 1.1
        self.assertAlmostEqual(self.baseXpoint['Zeff'], 1.1)

    @unittest.expectedFailure
    def test_match_nustar(self):
        self.baseXpoint.match_nustar(0.1)
        raise NotImplementedError('Value check')

    @unittest.expectedFailure
    def test_calc_nustar(self):
        self.baseXpoint.calc_nustar()
        raise NotImplementedError('Value check')

    @unittest.expectedFailure
    def test_setitems_nustar(self):
        self.baseXpoint['Nustar'] = 0.1
        self.assertAlmostEqual(self.baseXpoint['Nustar'], 0.1)
        raise NotImplementedError('Value check')

    @unittest.expectedFailure
    def test_match_tite(self):
        self.baseXpoint.match_tite(0.1)
        raise NotImplementedError('Value check')

    @unittest.expectedFailure
    def test_calc_tite(self):
        self.baseXpoint.calc_tite()
        self.baseXpoint['ions'][0]['T'] = 5
        self.assertRaisesRegex(Exception,
                                'Ions have non-equal temperatures',
                                self.baseXpoint.calc_tite)
        raise NotImplementedError('Value check')

    @unittest.expectedFailure
    def test_setitems_tite(self):
        self.baseXpoint['Ti_Te_rel'] = 0.1
        self.assertAlmostEqual(self.baseXpoint['Ti_Te_rel'], 0.1)
        raise NotImplementedError('Value check')

class TestQuaLiKizPlan_hyperedge(TestCase):
    def setUp(self):
        TestQuaLiKizXpoint.setUp(self)
        scan_dict = OrderedDict()
        keys = ['Ati', 'Ate', 'Ane', 'qx', 'smag', 'x', 'Ti_Te_rel', 'Zeff']
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

    @unittest.expectedFailure
    def test_setup(self):
        self.qualikizplan.setup()
        raise NotImplementedError('Consistency check')

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

    @unittest.expectedFailure
    def test_setup(self):
        self.qualikizplan.setup()
        raise NotImplementedError('Consistency check')

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
