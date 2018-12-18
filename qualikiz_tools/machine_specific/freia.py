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
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun

class Run(Run):
    def __init__(self, parent_dir, name, binaryrelpath,
                 stdout=None, stderr=None,
                 **kwargs):

        if stdout is None:
            stdout = Run.default_stdout
        if stderr is None:
            stderr = Run.default_stderr
        super().__init__(parent_dir, name, binaryrelpath,
                         stdout=stdout, stderr=stderr,
                         **kwargs)
        self.runstring = 'mpiexec'

    def to_batch_string(self, batch_dir):
        """ Create string to include in batch job

        This string will be used in the batch script file that runs the jobs.

        Args:
            batch_dir: Directory the batch script lives in. Needed to
                       generate the relative paths.
        """
        paths = []
        for path in [self.stdout, self.stderr]:
            if os.path.isabs(path):
                pass
            else:
                path = os.path.normpath(os.path.join(os.path.relpath(self.rundir, batch_dir), path))
            paths.append(path)
        if self.binaryrelpath is None:
            raise FileNotFoundError('No binary rel path specified, could not find link to QuaLiKiz binary in {!s}'.format(self.rundir))

        string = ' '.join([self.runstring ,
                           '-np $NSLOTS',
                           '-wdir'  , os.path.normpath(os.path.relpath(self.rundir, batch_dir)),
                                      './' + os.path.basename(self.binaryrelpath)])
        if self.stdout != 'STDOUT':
            string += ' > ' + paths[0]
        if self.stderr != 'STDERR':
            string += ' 2> ' + paths[1]
        return string


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
    attr = [
        'name',
        'stdout',
        'stderr'
    ]
    shell = '/bin/bash'
    run_class = Run
    defaults = {'stdout': 'qualikiz.batch.o*',
                'stderr': 'qualikiz.batch.e*',
                'cores_per_node': 16,
                }

    def __init__(self, parent_dir, name, runlist, tasks=None,
                 stdout=None, stderr=None,
                 HT=False,
                 vcores_per_task=2,
                 safetytime=1.5, style='sequential',
                 **kwargs):
        """ Initialize Freia batch job

        Args:
            - parent_dir:     Path to the directory this batchs folder
                              will be created
            - name:           Name of the Batch job. Will be the name
                              of the folder created
            - runlist:        List of Run instances included in this Batch

        Kwargs:
            - stdout:     File to write stdout to. By default 'stdout.batch'
            - stderr:     File to write stderr to. By default 'stderr.batch'
            - HT:         Hyperthreading on/off. Default=False
            - vcores_per_task: Amount of cores to use per task
            - safetytime: An extra factor that will be used in the calculation
                          of requested runtime. 1.5x by default
            - style:      How to glue the different runs together. Currently
                          only 'sequential' is used


        Calculated:
            - vcores_per_node: Amount of virtual cores per compute node.
            - vcores_per_task: Amount of virtual cores per MPI task. Should be 2
            - tasks_per_node:  Amount of MPI tasks per node
            - nodes:           Amount of nodes needed for this batch
            - maxtime:         Amount of time to request from submission system
        """
        for attribute in self.attr:
            if attribute  != 'nodes':
                if attribute in kwargs:
                    setattr(self, attribute, kwargs[attribute])
                elif attribute in self.defaults:
                    setattr(self, attribute, self.defaults[attribute])
                else:
                    setattr(self, attribute, None)

        super().__init__(parent_dir, name, runlist,
                         stdout=self.stdout, stderr=self.stderr)

        if HT is True:
            warn('No hyperthreading on Freia! Ignoring..')
        # HT 48 or no HT 24
        self.vcores_per_node = Run.defaults['cores_per_node']
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

        cmd = ' '.join([
            'cd',
            batch_dir,
            '&& qsub',
            self.scriptname,
        ])
        out = subprocess.check_output(cmd, shell=True)
        print(out.strip().decode('ascii'))

    def to_batch_file(self, filename=None, **kwargs):
        """ Writes sbatch script to file

        Kwargs:
            - filename: Name of the generated Batch file
                        [Default: qualikiz.batch]
        """
        if filename is None:
            filename = self.scriptname

        #sbatch_lines = ['#!' + self.shell + ' -l\n']
        #for attr, sbatch in zip(self.attr, self.sbatch):
        #    value = getattr(self, attr)
        #    if value is not None:
        #        line = '#SBATCH --' + sbatch + '=' + str(value) + '\n'
        #        sbatch_lines.append(line)
        lines = ['#$ -cwd\n']
        lines.append('#$ -pe openmpi {0:d}-{0:d}\n'.format(self.nodes * self.tasks_per_node))

        lines.append('\nexport OMP_NUM_THREADS=' +
                            str(self.vcores_per_task) + '\n')

        # Write sruns to file
        batchdir = os.path.join(self.parent_dir, self.name)
        for run_instance in self.runlist:
            lines.append('\n' + run_instance.to_batch_string(batchdir))
        lines.append('\n')

        with open(os.path.join(batchdir, filename), 'w') as file:
            file.writelines(lines)

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
