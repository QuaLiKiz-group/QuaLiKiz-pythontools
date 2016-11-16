#!/usr/bin/env python3
"""
Copyright Dutch Institute for Fundamental Energy Research (2016)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import os
import sys
import inspect
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizBatch, QuaLiKizRun
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
# First, we need to know where the binary and qualikiz_tools folder
# reside
name = 'mini'
binreldir = os.path.relpath(os.path.join(rootdir, '../QuaLiKiz'),
                            os.path.join(runsdir, name))
pythonreldir = os.path.relpath(PATH,
                               os.path.join(runsdir, name))

# Create the run. By not passing it a QuaLiKizPlan, it will use the
# parameters_template.json file
run = QuaLiKizRun(runsdir, name,
                  binreldir)
runlist = [run]

# Our batch only contains one run. Let's run on the debug queue
batch = QuaLiKizBatch(runsdir, name, runlist, 24, partition='debug')
batch.prepare()
batch.generate_input()

resp = input('Submit job to queue? [Y/n]')
if resp == '' or resp == 'Y' or resp == 'y':
    batch.queue_batch()
