#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(sys.path[0]))
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizBatch, QuaLiKizRun
from qualikiz_tools.machine_specific.slurm import Srun, Sbatch

command = 'go'
if len(sys.argv) == 2:
    if sys.argv[1] != '':
        command = sys.argv[1]

batch = QuaLiKizBatch.from_dir('.')

if command.startswith('input'):
    batch.generate_input()

if command.endswith('go'):
    batch.clean()
    batch.queue_batch()

