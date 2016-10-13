#!/usr/bin/env python3
"""
Copyright Dutch Institute for Fundamental Energy Research (2016)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import os
import sys
import inspect
from qualikiz.qualikizrun import QuaLiKizBatch, QuaLiKizRun

dirname = 'runs'
if len(sys.argv) == 2:
    if sys.argv[1] != '':
        dirname = sys.argv[1]

# We know where this script lives, so we can find the rootdir like this
rootdir = os.path.abspath(
    os.path.join(os.path.abspath(inspect.getfile(inspect.currentframe())),
                 '../../../'))
runsdir = os.path.join(rootdir, dirname)
binreldir = os.path.relpath(os.path.join(rootdir, 'QuaLiKiz'),
                            os.path.join(runsdir, 'mini'))
pythonreldir = os.path.relpath(os.path.join(rootdir, 'tools/qualikiz'),
                               os.path.join(runsdir, 'mini'))

run = QuaLiKizRun(runsdir, 'mini',
                  binreldir)
runlist = [run]
batch = QuaLiKizBatch(runsdir, 'mini', runlist, 24, partition='debug')
batch.prepare()
batch.generate_input()

resp = input('Submit job to queue? [Y/n]')
if resp == '' or resp == 'Y' or resp == 'y':
    batch.queue_batch()
