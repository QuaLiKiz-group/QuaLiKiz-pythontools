from subprocess import PIPE, Popen as popen
from unittest import TestCase, skip
import logging
import os
from itertools import zip_longest
import copy

@skip('Edison specific test not re-written to new structure')
def setUpModule():
    from qualikiz_tools.machine_specific.slurm import Srun, Sbatch

logging.basicConfig(level=logging.DEBUG)
class TestSrun(TestCase):
    def setUp(self):
        self.srun = Srun('TestBinary', 24, chdir='..',
                         stdout='/dev/stdout', stderr='/dev/stderr')

    def test_srun_deepcopy(self):
        srun_new = copy.deepcopy(self.srun)
        self.assertEqual(self.srun, srun_new)

    def test_srun_equality(self):
        srun_new = copy.deepcopy(self.srun)
        self.assertEqual(self.srun, srun_new)
        self.assertTrue(self.srun.__eq__(srun_new))
        self.assertFalse(self.srun.__ne__(srun_new))
        self.assertIs(self.srun.__eq__(None), NotImplemented)
        self.assertIs(self.srun.__ne__(None), NotImplemented)

    def test_srun_to_string(self):
        srun_string = self.srun.to_string()
        self.assertEqual(srun_string, 'srun -n 24 --chdir .. ' +
                      '--output /dev/stdout --error /dev/stderr TestBinary')

    def test_srun_from_string(self):
        srun_string = ('srun -n 24 --chdir .. ' +
                       '--output /dev/stdout --error /dev/stderr TestBinary')
        srun_new = Srun.from_string(srun_string)
        self.assertEqual(self.srun, srun_new)


class TestSbatch(TestCase):
    def setUp(self):
        srun = Srun('TestBinary', 24, chdir='..',
                    stdout='/dev/stdout', stderr='/dev/stderr')
        srun_list = [srun, srun]
        self.sbatch = Sbatch(srun_list, 'TestBatch', 24, '00:30:00',
                        stdout='/dev/stdout', stderr='/dev/stderr',
                        filesystem='project', partition='debug',
                        HT=True, repo='m2116')

    def test_initialize_sbatch(self):
        srun_list = []
        sbatch = Sbatch(srun_list, 'TestBatch', 1, '00:30:00',
                        stdout='/dev/stdout', stderr='/dev/stderr',
                        filesystem='project', partition='debug',
                        HT=False)

    def test_sbatch_deepcopy(self):
        sbatch_new = copy.deepcopy(self.sbatch)
        self.assertEqual(self.sbatch, sbatch_new)

    def test_sbatch_equality(self):
        sbatch_new = copy.deepcopy(self.sbatch)
        self.assertEqual(self.sbatch, sbatch_new)
        self.assertTrue(self.sbatch.__eq__(sbatch_new))
        self.assertFalse(self.sbatch.__ne__(sbatch_new))
        self.assertIs(self.sbatch.__eq__(None), NotImplemented)
        self.assertIs(self.sbatch.__ne__(None), NotImplemented)

    def test_sbatch_to_file(self):
        self.sbatch.to_file('testbatch')

        sbatch_created_file = []
        with open('testbatch') as sbatchfile:
            for line in sbatchfile:
                sbatch_created_file.append(line)

        sbatch_test_file = ['#!/bin/bash -l\n',
                            '#SBATCH --nodes=1\n',
                            '#SBATCH --time=00:30:00\n',
                            '#SBATCH --partition=debug\n',
                            '#SBATCH --ntasks-per-node=24\n',
                            '#SBATCH --cpus-per-task=2\n',
                            '#SBATCH --license=project\n',
                            '#SBATCH --job-name=TestBatch\n',
                            '#SBATCH --account=m2116\n',
                            '#SBATCH --error=/dev/stderr\n',
                            '#SBATCH --output=/dev/stdout\n',
                            '#SBATCH --qos=normal\n',
                            '\n',
                            'export OMP_NUM_THREADS=2\n',
                            '\n',
                            'srun -n 24 --chdir .. --output /dev/stdout ' +
                            '--error /dev/stderr TestBinary\n',
                            'srun -n 24 --chdir .. --output /dev/stdout ' +
                            '--error /dev/stderr TestBinary\n']
        for test, created in zip_longest(sbatch_test_file,
                                         sbatch_created_file):
            self.assertEqual(test, created)

    def test_sbatch_from_file(self):
        self.sbatch.to_file('testbatch')
        sbatch_new = self.sbatch.from_file('testbatch')
        self.assertEqual(self.sbatch, sbatch_new)

    def tearDown(self):
        try:
            os.remove('testbatch')
        except FileNotFoundError:
            pass
