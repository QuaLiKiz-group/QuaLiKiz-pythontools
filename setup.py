"""Packaging settings."""


from codecs import open
from os.path import abspath, dirname, join
from subprocess import call

from setuptools import Command, find_packages, setup

from qualikiz_tools import __version__


this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test', '--cov=qualikiz_tools', '--cov-report=term-missing',
                      '--ignore=lib/'])
        raise SystemExit(errno)


setup(
    name = 'qualikiz_pythontools',
    version = __version__,
    description = 'Python tools for the QuaLiKiz Quasi-linear gyrokinetic code.',
    long_description = long_description,
    url = 'https://github.com/QuaLiKiz-group/QuaLiKiz',
    author = 'Karel van de Plassche',
    author_email = 'karelvandeplassche@gmail.com',
    license = 'CeCill v2.1',
    classifiers = [
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: CeCILL v2.1',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
    ],
    keywords = 'cli',
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires = ['docopt', 'tabulate'],
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    entry_points = {
        'console_scripts': [
            'qualikiz_tools=qualikiz_tools.cli:main',
        ],
    },
    cmdclass = {'test': RunTests},
)
