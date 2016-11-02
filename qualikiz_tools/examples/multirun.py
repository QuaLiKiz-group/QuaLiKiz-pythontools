#!/usr/bin/env python3
"""
Copyright Dutch Institute for Fundamental Energy Research (2016)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import sys
import os
import inspect
import copy
from collections import OrderedDict

import numpy as np

from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizBatch, QuaLiKizRun
from qualikiz_tools.qualikiz_io.inputfiles import QuaLiKizPlan
from qualikiz_tools import __path__ as PATH  
PATH = PATH[0]

dirname = '../runs'
if len(sys.argv) == 2:
    if sys.argv[1] != '':
        dirname = sys.argv[1]
# We assume the QuaLiKiz_pythontoolsdir lives inside the QuaLiKiz root
rootdir = os.path.dirname(PATH)

# Find some of the paths we need
runsdir = os.path.join(rootdir, dirname)
print(runsdir)
bindir = os.path.join(rootdir, '../QuaLiKiz')
templatepath = os.path.join(rootdir, 'qualikiz_tools/qualikiz_io/parameters_template.json')

# Load the default QuaLiKiz plan we will use as base
qualikiz_plan_base = QuaLiKizPlan.from_json(templatepath)
print(qualikiz_plan_base['xpoint_base']['special']['kthetarhos'])
dimn = len(qualikiz_plan_base['xpoint_base']['special']['kthetarhos'])

# We will use a physically relevant base scan
qualikiz_plan_base['scan_dict'] = OrderedDict([('Ati', [2.75, 3.5, 4.25, 5.0, 5.75, 6.5, 7.25, 8.0]), ('Ate', [2.75, 3.5, 4.25, 5.0, 5.75, 6.5, 7.25, 8.0]), ('Ane', [-1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]), ('qx', [1.5, 2.0, 2.5, 3.0, 4.0, 5.0])])
qualikiz_plan_base['scan_type'] = 'hyperrect'
qualikiz_plan_base['xpoint_base']['kthetarhos'] = [0.1, 0.175, 0.25, 0.325, 0.4, 0.5, 0.6, 0.8, 1.0, 2.0, 3.5, 6.0, 10.5, 15.0, 19.5, 24.0, 30.0, 36.0]
print (qualikiz_plan_base)

# Set up multiple runs. For example, scanning over maxpoints:
maxpoints = [5e5, 5e4, 5e3, 1e3]
cores = 4 * 24
batch_list = []
for maxpts in maxpoints:
    name = 'maxpts' + str(maxpts)

    # Because we will overwrite this dict every loop, no need to deepcopy
    qualikiz_plan_base['xpoint_base']['maxpts'] = maxpts

    binreldir = os.path.relpath(bindir,
                                os.path.join(runsdir, name))
    run = QuaLiKizRun(runsdir, name,
                      binreldir,
                      qualikiz_plan=qualikiz_plan_base)
    # Let us keep a single run per batch
    runlist = [run]
    batch = QuaLiKizBatch(runsdir, name, runlist,
                          cores, partition='debug')
    batch.prepare(overwrite_batch=True)
    batch_list.append(batch)

print('Generating input files', end='', flush=True)
for batch in batch_list:
    batch.generate_input(dotprint=True)
print('\n')
resp = input('Submit all jobs in runsdir to queue? [Y/n]')
if resp == '' or resp == 'Y' or resp == 'y':
    for batch in batch_list:
        batch.queue_batch()
