"""
Copyright Dutch Institute for Fundamental Energy Research (2016)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
from warnings import warn
import os
import subprocess

import numpy as np
from IPython import embed

from qualikiz_tools.machine_specific.system import Batch
from qualikiz_tools.machine_specific.bash import Run
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch
from qualikiz_tools.qualikiz_io.inputfiles import QuaLiKizPlan

THISUSER='whoami'
BATCHSHARE='ypmatch kplass batchshare'
MAILADDRESS=THISUSER
RAM=0
LINENUMBER=0
SHELL=0
NUMPROC=0
JOBNAME='basename $CMDFILE'

class Batch(Batch):
    """ Defines a batch job

    This class uses the OpenMP/MPI parameters as defined by Edison,
    but could in principle be extented to support more machines.

    Class Variables:
        - attr:             All possible attributes as defined by Edison
        - sbatch:           Names of attributes as they are in the sbatch file
        - shell:            The shell to use for sbatch scripts. Usually bash
    """
    # pylint: disable=too-many-instance-attributes
    shell = '/bin/bash'
    run_class = Run
    defaults = {'stdout': 'stdout.batch',
                'stderr': 'stderr.batch'}

    def __init__(self, parent_dir, name, runlist, tasks=None, maxtime=None,
                 stdout=None, stderr=None,
                 filesystem=None, partition=None,
                 qos=None, repo=None, HT=None,
                 vcores_per_task=2,
                 safetytime=1.5, style='sequential'):
        """ Initialize Edison batch job

        Args:
            - srun_instances: List of Srun instances included in the Sbatch job
            - name:           Name of the Sbatch job
            - tasks:          Amount of MPI tasks
            - maxtime:        Maximum walltime needed
            - ncpu:      Amount of cpus to be used

        Kwargs:
            - stdout:     File to write stdout to. By default 'stdout.batch'
            - stderr:     File to write stderr to. By default 'stderr.batch'
            - filesystem: The default filesystem to use. Usually SCRATCH
            - partition:  Partition to run on, for example 'debug'. By default
                          'regular'
            - qos:        Priority in the queue. By default 'normal'
            - repo:       The default repo to bill hours to. Usually None
            - HT:         Hyperthreading on/off. Default=True
            - vcores_per_task: Amount of cores to use per task
            - safetytime: An extra factor that will be used in the calculation
                          of requested runtime. 1.5x by default
            - style:      How to glue the different runs together. Currently
                          only 'sequential' is used


        Calculated:
            - threads_per_core: amount of OMP threads per physical core
            - threads_per_node: amount of OMP threads per compute node
            - sockets_per_node: Amount of sockets in one compute node
            - cores_per_socket: Amount of physical CPU cores in one socket
            - cores_per_node:   Amount of physical CPU cores in one node
        """
        self.parent_dir = parent_dir

        self.filesystem = filesystem
        self.repo = repo
        self.qos = qos
        self.maxtime = maxtime
        self.partition = partition
        self.name = name
        self.runlist = runlist
        self.stdout = stdout
        self.stderr = stderr
        for name in ['filesystem', 'repo', 'qos', 'maxtime', 'partition', 'name', 'runlist', 'stdout', 'stderr']:
            if getattr(self, name) is None:
                if name in self.defaults:
                    setattr(self, name, self.defaults[name])

        if HT:
            vcores_per_core = 2  # Per definition, not for KNL..
        else:
            vcores_per_core = 1
        # HT 48 or no HT 24
        self.vcores_per_node = Run.cores_per_node * vcores_per_core
        self.vcores_per_task = vcores_per_task  # 2, as per QuaLiKiz
        self.tasks_per_node = int(self.vcores_per_node / self.vcores_per_task)
        if style == 'sequential':
            task_list = [run.tasks for run in self.runlist]
            if tasks is None:
                tasks = np.max(task_list)

            vcores = self.vcores_per_task * tasks

            totwallsec = np.sum([run.estimate_walltime(vcores) for run in self.runlist])
            totwallsec *= safetytime
            m, s = divmod(totwallsec, 60)
            h, m = divmod((m + 1), 60)

            # TODO: generalize for non-edison machines
            if partition == 'debug' and (h >= 1 or m >= 30):
                warn('Walltime requested too high for debug partition')
            self.maxtime = ("%d:%02d:%02d" % (h, m, s))

            self.nodes = self.calc_nodes(tasks, self.tasks_per_node)

        else:
            raise NotImplementedError('Style {!s} not implemented yet.'.format(style))

    @staticmethod
    def calc_nodes(tasks, tasks_per_node):
        nodes, remainder = divmod(tasks, tasks_per_node)
        nodes = int(nodes)
        if remainder != 0:
            nodes += 1
            warn(str(tasks) + ' tasks not evenly divisible over ' +
                 str(tasks_per_node) + ' tasks per node. Using ' +
                 str(nodes) + ' nodes.')

        return nodes

    def launch(self):
        self.inputbinaries_exist()
        self.clean()
        paths = []
        batch_dir = os.path.join(self.parent_dir, self.name)

        cmd = ' '.join(['sbatch'    ,
                           '--chdir'  , batch_dir     ,
                                        self.scriptname])
        out = subprocess.check_output(cmd, shell=True)
        print(out.strip().decode('ascii'))

    def to_batch_file(self, filename=None, **kwargs):
        """ Writes sbatch script to file

        Args:
            - path: Path of the sbatch script file.
        """
        if filename is None:
            filename = self.scriptname

        sbatch_lines = ['#!' + self.shell + ' -l\n']
        for attr, sbatch in zip(self.attr, self.sbatch):
            value = getattr(self, attr)
            if value is not None:
                line = '#SBATCH --' + sbatch + '=' + str(value) + '\n'
                sbatch_lines.append(line)

        sbatch_lines.append('\nexport OMP_NUM_THREADS=' +
                            str(self.vcores_per_task) + '\n')

        # Write sruns to file
        for run_instance in self.runlist:
            sbatch_lines.append('\n' + run_instance.to_batch_string())
        sbatch_lines.append('\n')

        batchdir = os.path.join(self.parent_dir, self.name)
        with open(os.path.join(batchdir, filename), 'w') as file:
            file.writelines(sbatch_lines)

    @classmethod
    def from_batch_file(cls, path, **kwargs):
        """ Reconstruct sbatch from sbatch file """
        srun_strings = []
        batch_dict = {}
        with open(path, 'r') as file:
            for line in file:
                if line.startswith('#SBATCH --'):
                    line = line.lstrip('#SBATCH --')
                    name, value = line.split('=')
                    value = str_to_number(value.strip())
                    if name in cls.sbatch:
                        batch_dict[cls.attr[cls.sbatch.index(name)]] = value
                        #setattr(new, cls.attr[cls.sbatch.index(name)], value)
                if line.startswith('srun'):
                    srun_strings.append(line)

        #try:
        #    getattr(new, 'repo')
        #except AttributeError:
        #    setattr(new, 'repo', None)

        #new.vcores_per_node = new.tasks_per_node * new.vcores_per_task
        batch_dir = os.path.dirname(os.path.abspath(path))
        batch_name = os.path.basename(batch_dir)
        batch_parent = os.path.dirname(batch_dir)
        try:
            runlist = []
            for srun_string in srun_strings:
                runlist.append(cls.run_class.from_batch_string(batch_dir, srun_string))
        except FileNotFoundError:
            raise Exception('Could not reconstruct run from string: {!s}'.format(srun_string))

        check_vars = {}
        for var in ['nodes', 'tasks_per_node', 'name']:
            if var in batch_dict:
                check_vars[var] = batch_dict.pop(var)

        batch = Batch(batch_parent, batch_name, runlist, **batch_dict)
        return batch

    @classmethod
    def from_dir(cls, batchdir, run_kwargs=None, batch_kwargs=None):
        if batch_kwargs is None:
            batch_kwargs = {}
        if run_kwargs is None:
            run_kwargs = {}
        path = os.path.join(batchdir, cls.scriptname)
        try:
            new = cls.from_batch_file(path, **batch_kwargs)
        except FileNotFoundError:
            warn('{!s} not found! Falling back to subdirs'.format(path))
            new = cls.from_subdirs(batchdir, run_kwargs=run_kwargs)
        return new


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self == other
        return NotImplemented


def str_to_number(string):
    """ Convert a string in a float or int if possible """
    try:
        value = float(string)
    except ValueError:
        value = string
    else:
        if value.is_integer:
            value = int(value)
    return value
