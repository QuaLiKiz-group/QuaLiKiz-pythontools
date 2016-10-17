"""Tests for our main skele CLI module."""


from subprocess import PIPE, Popen as popen
from unittest import TestCase

from qualikiz_tools import __version__ as VERSION


class TestHelp(TestCase):
    def test_returns_usage_information(self):
        output = popen(['qualikiz_tools', '-h'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output.decode('UTF-8'))

        output = popen(['qualikiz_tools', '--help'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output.decode('UTF-8'))

        output = popen(['qualikiz_tools', 'help'], stdout=PIPE).communicate()[0]
        self.assertTrue('Usage:' in output.decode('UTF-8'))


class TestVersion(TestCase):
    def test_returns_version_information(self):
        output = popen(['qualikiz_tools', '--version'], stdout=PIPE).communicate()[0]
        self.assertEqual(output.strip().decode('UTF-8'), VERSION)
