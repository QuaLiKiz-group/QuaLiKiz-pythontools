"""Tests for our `skele hello` subcommand."""


from subprocess import PIPE, Popen as popen
from unittest import TestCase, skip
import os
import shutil
from qualikiz_tools import __path__ as PATH  
PATH = PATH[0]


class TestCreate(TestCase):
    def test_returns_usage_information(self):
        output = popen(['qualikiz_tools', 'create', '-h'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output.decode('UTF-8'))

        output = popen(['qualikiz_tools', 'create', '--help'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output.decode('UTF-8'))

        output = popen(['qualikiz_tools', 'create', 'help'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output.decode('UTF-8'))

    def test_returns_multiple_lines(self):
        output = popen(['qualikiz_tools', 'create', 'help'], stdout=PIPE).communicate()[0]
        output = output.decode('UTF-8')
        lines = output.split('\n')
        self.assertTrue(len(lines) != 1)

@skip('Not included in CLI')
class TestMini(TestCase):
    def test_mini(self):
        if not os.path.exists('../QuaLiKiz'):
            with open('../QuaLiKiz', 'w+') as __:
                pass
            self.addCleanup(os.remove, '../QuaLiKiz')
        mini_path = os.path.join(PATH, 'examples', 'mini.py')
        with open('/dev/null', 'wb') as null:
            process = popen(['qualikiz_tools', 'create', 'mini', 'testmini'],
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

@skip('Not included in CLI')
class TestPerformance(TestCase):
    binrelname = '../QuaLiKiz+pat'
    def test_performance(self):
        if not os.path.exists(self.binrelname):
            with open(self.binrelname, 'w+') as __:
                pass
            self.addCleanup(os.remove, self.binrelname)
        performance_path = os.path.join(PATH, 'examples', 'performance.py')
        with open('/dev/null', 'wb') as null:
            process = popen(['qualikiz_tools', 'create', 'performance', 'testperformance'],
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
