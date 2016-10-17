from subprocess import PIPE, Popen as popen
import unittest
from unittest import TestCase
import copy
import os
import shutil

from qualikiz_tools import __path__ as PATH
PATH = PATH[0]

class TestMini(TestCase):
    def test_mini(self):
        if not os.path.exists('../QuaLiKiz'):
            with open('../QuaLiKiz', 'w+') as __:
                pass
            self.addCleanup(os.remove, '../QuaLiKiz')
        mini_path = os.path.join(PATH, 'examples', 'mini.py')
        with open('/dev/null', 'wb') as null:
            process = popen(['python3', mini_path, 'testmini'],
                            stdin=PIPE, stdout=null, stderr=PIPE)
        output = process.communicate(input=b'n\n')
        if output[1].decode('UTF-8') is not '':
            print('STDERR = ' + output[1].decode('UTF-8'))
            raise Exception('Error while running process')

    def tearDown(self):
        pass
        try:
            shutil.rmtree('testmini')
        except FileNotFoundError:
            pass

class TestPerformance(TestCase):
    binrelname = '../QuaLiKiz+pat'
    def test_performance(self):
        if not os.path.exists(self.binrelname):
            with open(self.binrelname, 'w+') as __:
                pass
            self.addCleanup(os.remove, self.binrelname)
        performance_path = os.path.join(PATH, 'examples', 'performance.py')
        with open('/dev/null', 'wb') as null:
            process = popen(['python3', performance_path, 'testperformance'],
                            stdin=PIPE, stdout=null, stderr=PIPE)
        output = process.communicate(input=b'n\n')
        if output[1].decode('UTF-8') is not '':
            print('STDERR = ' + output[1].decode('UTF-8'))
            raise Exception('Error while running process')

    def tearDown(self):
        try:
            shutil.rmtree('testperformance')
        except FileNotFoundError:
            pass
