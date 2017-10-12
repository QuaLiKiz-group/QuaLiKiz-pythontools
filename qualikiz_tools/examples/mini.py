#!/usr/bin/env python3
"""
Copyright Dutch Institute for Fundamental Energy Research (2016)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import os
import sys
import inspect
from qualikiz_tools.machine_specific.bash import Batch, Run
from qualikiz_tools import __path__ as PATH
PATH = PATH[0]

dirname = '../runs'
if len(sys.argv) == 2:
    if sys.argv[1] != '':
        dirname = sys.argv[1]
# We assume the QuaLiKiz_pythontoolsdir lives inside the QuaLiKiz root
rootdir = os.path.dirname(PATH)

# We'll create a folder called 'runs' in the rootdir
runsdir = os.path.join(rootdir, dirname)

# We'll make a folder 'mini' inside the 'runs' dir with our example
# First, we need to know where the binary lives relative to the folder
name = 'mini'
binreldir = os.path.relpath(os.path.join(rootdir, '../QuaLiKiz'),
                            os.path.join(runsdir, name))

# Create the run. By not passing it a QuaLiKizPlan, it will use the
# parameters_template.json file
run = Run(runsdir, name, binreldir)
runlist = [run]

# Let's also create a batch script:
batch = Batch(runsdir, name, runlist)
batch.prepare()
batch.generate_input()

resp = input('Run job? [Y/n]')
if resp == '' or resp == 'Y' or resp == 'y':
    batch.launch()
