
from subprocess import PIPE, Popen as popen
import unittest
from unittest import TestCase
import copy
import os
import shutil

from qualikiz_tools.qualikiz_io.inputfiles import *
from qualikiz_tools.qualikiz_io.qualikizrun import *

class TestPathException(TestCase):
    def test(self):
        with self.assertRaises(PathException):
            raise PathException('made up')

class TestQuaLiKizRun(TestCase):
    kthetarhos = [0.1, 2.2, 4.4, 6.6, 8.8, 11., 13.2, 15.4,
                  17.6, 19.8, 22., 24.2, 26.4, 28.6, 30.8, 33.]
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
    ions = IonList(ion_0, ion_1)
    ions.append(Ion(**ion_2))
    elec = Electron(**part)

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
    
    defaults = {}
    defaults.update(meta)
    defaults.update(geometric)
    norm = {'ninorm1': False,
            'Ani1':    False,
            'QN_grad': False,
            'x_rho':   False}
    defaults.update(norm)
    baseXpoint = QuaLiKizXpoint(kthetarhos,
                            elec, ions, **defaults)

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
    qualikizplan = QuaLiKizPlan(scan_dict, 'hyperedge', baseXpoint)
    def setUp(self):
        with open('./testQuaLiKiz', 'w+') as __:
            pass
        self.qualikizrun = QuaLiKizRun(os.path.abspath('testrunsdir'),
                                       'testrun',
                                       '../../testQuaLiKiz',
                                       qualikiz_plan=TestQuaLiKizRun.qualikizplan)

    def test_initialize(self):
        pass

    def test_deepcopy(self):
        newrun = copy.deepcopy(self.qualikizrun)
        self.assertEqual(self.qualikizrun, newrun)
        newrun.stdout = 'test'
        self.assertNotEqual(self.qualikizrun, newrun)

    def test_prepare(self):
        self.qualikizrun.prepare()
        rundir = self.qualikizrun.rundir
        self.assertTrue(os.path.exists(os.path.join(rundir, 'output')))
        self.assertTrue(os.path.exists(os.path.join(rundir, 'output',
                                                    'primitive')))
        self.assertTrue(os.path.exists(os.path.join(rundir, 'input')))
        self.assertTrue(os.path.exists(os.path.join(rundir, 'testQuaLiKiz')))
        self.assertTrue(os.path.exists(os.path.join(rundir, 'qualikiz_tools')))
        self.assertTrue(os.path.exists(os.path.join(rundir, 'run.py')))
        self.assertTrue(os.path.exists(os.path.join(rundir, 'parameters.json')))

    def test_generate_input(self):
        self.qualikizrun.prepare()
        self.qualikizrun.generate_input()
        rundir = self.qualikizrun.rundir
        in_input = os.listdir(os.path.join(rundir, 'input'))
        self.assertEqual(len(in_input), 45)

    def test_inputbinaries_exist(self):
         self.qualikizrun.prepare()
         with warnings.catch_warnings():
             warnings.simplefilter("ignore")
             self.assertFalse(self.qualikizrun.inputbinaries_exist())
         self.qualikizrun.generate_input()
         self.assertTrue(self.qualikizrun.inputbinaries_exist())

    def test_from_dir(self):
        self.qualikizrun.prepare()
        binaryrelpath = '../../testQuaLiKiz'
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            newrun = QuaLiKizRun.from_dir(self.qualikizrun.rundir, binaryrelpath)
        self.assertEqual(self.qualikizrun, newrun)

    def test_clean(self):
        self.qualikizrun.prepare()
        outputdir = os.path.join(self.qualikizrun.rundir,
                                 self.qualikizrun.outputdir)
        primitivedir = os.path.join(self.qualikizrun.rundir,
                                    self.qualikizrun.outputdir)
        debugdir = os.path.join(self.qualikizrun.rundir,
                                self.qualikizrun.outputdir)
        stdout = os.path.join(self.qualikizrun.rundir,
                              self.qualikizrun.stdout)
        stderr = os.path.join(self.qualikizrun.rundir,
                              self.qualikizrun.stderr)
        testfiles = [os.path.join(outputdir, 'test.dat'),
                     os.path.join(primitivedir, 'test.dat'),
                     os.path.join(debugdir, 'test.dat'),
                     stdout,
                     stderr]
        for testfile in testfiles:
            with open(testfile, 'w+') as __:
                pass
        self.qualikizrun.clean()
        for testfile in testfiles:
            self.assertFalse(os.path.exists(testfile))

    def tearDown(self):
        os.remove('./testQuaLiKiz')
        try:
            shutil.rmtree('./testrunsdir')
        except FileNotFoundError:
            pass

class TestQuaLiKizBatch(TestCase):
    def setUp(self):
        TestQuaLiKizRun.setUp(self)
        with open('./testQuaLiKiz', 'w+') as __:
            pass
        testrun_0 = QuaLiKizRun(os.path.abspath('testbatchsdir/testbatch'),
                                'testrun_0',
                                '../../../testQuaLiKiz',
                                qualikiz_plan=TestQuaLiKizRun.qualikizplan)
        testrun_1 = QuaLiKizRun(os.path.abspath('testbatchsdir/testbatch'),
                                'testrun_1',
                                '../../../testQuaLiKiz',
                                qualikiz_plan=TestQuaLiKizRun.qualikizplan)

        self.qualikizbatch = QuaLiKizBatch(
            os.path.abspath('testbatchsdir'),
            'testbatch',
            [testrun_0, testrun_1],
            24)

    def test_initialize(self):
        pass

    def test_prepare(self):
        self.qualikizbatch.prepare()

    def test_generate_input(self):
        self.qualikizbatch.prepare()
        self.qualikizbatch.generate_input()

    def test_from_dir(self):
        self.qualikizbatch.prepare()
        self.qualikizbatch.generate_input()
        batchdir = os.path.join(self.qualikizbatch.batchsdir,
                                self.qualikizbatch.name)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            newbatch = QuaLiKizBatch.from_dir(batchdir)
        self.assertEqual(self.qualikizbatch, newbatch)

    def test_from_dir_recursive(self):
        self.qualikizbatch.prepare()
        self.qualikizbatch.generate_input()
        searchdir = self.qualikizbatch.batchsdir
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            newbatchs = QuaLiKizBatch.from_dir_recursive(searchdir)
        self.assertEqual(len(newbatchs), 1)
        self.assertEqual(self.qualikizbatch, newbatchs[0])

    def test_clean(self):
        self.qualikizbatch.prepare()
        batchdir = os.path.join(self.qualikizbatch.batchsdir,
                                self.qualikizbatch.name)
        testfiles = [os.path.join(batchdir, QuaLiKizBatch.batchinfofile),
                     os.path.join(batchdir, Sbatch.default_stdout),
                     os.path.join(batchdir, Sbatch.default_stderr)]

        for testfile in testfiles:
            with open(testfile, 'w+') as __:
                pass
        self.qualikizbatch.clean()
        for testfile in testfiles:
            self.assertFalse(os.path.exists(testfile))

    def tearDown(self):
        try:
            shutil.rmtree('testbatchsdir')
        except FileNotFoundError:
            pass
        os.remove('./testQuaLiKiz')

