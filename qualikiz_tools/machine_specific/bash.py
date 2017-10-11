"""
Copyright Dutch Institute for Fundamental Energy Research (2016-2017)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
from warnings import warn
import os
import stat
from .system import System
from ..qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch
import subprocess
import multiprocessing as mp

class Batch(System.Batch):
    """ Defines a batch job

    This class uses the OpenMP/MPI parameters as defined by Edison,
    but could in principle be extented to support more machines.

    Class Variables:
        - shell:            The shell to use for sbatch scripts. Usually bash
    """
    shell = '/bin/bash'

    def __init__(self, parent_dir, name, runlist, tasks=None,
                 stdout=None, stderr=None,
                 HT=True,
                 vcores_per_task=2,
                 style='sequential'):
        """ Initialize Edison batch job

        Args:
            - srun_instances: List of Srun instances included in the Sbatch job
            - name:           Name of the Sbatch job
            - tasks:          Amount of MPI tasks
            - ncpu:           Amount of cpus to be used

        Kwargs:
            - stdout:     File to write stdout to. By default 'stdout.batch'
            - stderr:     File to write stderr to. By default 'stderr.batch'
            - HT:         Hyperthreading on/off. Default=True
            - style:      How to glue the different runs together. Currently
                          only 'sequential' is used
        """

        super().__init__(parent_dir, name, runlist)

        if style == 'sequential':
            pass
        else:
            raise NotImplementedError('Style {!s} not implemented yet.'.format(style))

    def to_batch_file(self, path):
        """ Writes sbatch script to file

        Args:
            - path: Path of the sbatch script file.
        """
        batch_lines = ['#!' + self.shell + '\n\n']

        # Write sruns to file
        batch_lines.append(self.runlist[0].to_batch_string(os.path.dirname(path)))
        for run in self.runlist[1:]:
            batch_lines.append(' &&\n' + run.to_batch_string(os.path.dirname(path)))

        with open(path, 'w') as file:
            file.writelines(batch_lines)

        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    @classmethod
    def from_batch_file(cls, path):
        """ Reconstruct sbatch from sbatch file """
        run_strings = []
        with open(path, 'r') as file:
            for line in file:
                if line.startswith(Run.runstring):
                    run_strings.append(line)

        runlist = []
        for run_string in run_strings:
            runlist.append(Run.from_batch_string(run_string))
        name = os.path.basename(os.path.dirname(path))
        parent_dir = os.path.dirname(os.path.dirname(path))

        return Batch(parent_dir, name, runlist)

    def launch(self):
        for run in self.runlist:
            run.inputbinaries_exist()
        # Check if batch script is generated
        batchdir = os.path.join(self.parent_dir, self.name)
        batchpath = os.path.join(batchdir, self.scriptname)
        if not os.path.exists(batchpath):
            raise Exception('Batch script does not exist!')

        self.clean()

        cmd = ' '.join(['cd', batchdir, '&& bash', self.scriptname])
        stdout = open(os.path.join(batchdir, self.stdout), 'w')
        stderr = open(os.path.join(batchdir, self.stderr), 'w')
        subprocess.check_call(cmd, shell=True, stdout=stdout, stderr=stderr)


#    def __eq__(self, other):
#        if isinstance(other, self.__class__):
#            return self.__dict__ == other.__dict__
#        return NotImplemented
#
#    def __ne__(self, other):
#        if isinstance(other, self.__class__):
#            return not self == other
#        return NotImplemented


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


class Run(System.Run):
    runstring = 'mpirun'
    """ Defines the run command """

    def __init__(self, parent_dir, name, binaryrelpath,
                 qualikiz_plan=None, stdout=None, stderr=None, verbose=False,
                 tasks=None, **kwargs):
        """ Initializes the Srun class

        Args:
            - binary_name: The name of the binary relative to where
                           the sbatch script will be
            - tasks:       Amount of MPI tasks needed for the job
        Kwargs:
            - chdir:  Dir to change to before running the command
            - stdout: Standard target of redirect of STDOUT
            - stderr: Standard target of redirect of STDERR
        """
        super().__init__(parent_dir, name, binaryrelpath,
                         qualikiz_plan=qualikiz_plan,
                         stdout=stdout, stderr=stderr,
                         verbose=verbose)
        if tasks is None:
            ncpu = mp.cpu_count()
            HT = True
            self.tasks = self.calculate_tasks(ncpu, HT=HT)
        else:
            self.tasks = tasks

    def to_batch_string(self, batch_parent_dir):
        """ Create the run string """
        paths = []
        for path in [self.stdout, self.stderr]:
            if os.path.isabs(path):
                pass
            else:
                path = os.path.normpath(os.path.join(os.path.relpath(self.rundir, batch_parent_dir), path))
            paths.append(path)

        string = ' '.join([self.runstring ,
                           '-n'     , str(self.tasks) ,
                           '-wdir'  , self.rundir     ,
                                      './' + os.path.basename(self.binaryrelpath) ,
                           '>'      , paths[0]        ,
                           '2>'     , paths[1]        ,
        ])
        return string

    @classmethod
    def from_batch_string(cls, string):
        """ Reconstruct the Run from a string """
        split = string.split(' ')
        tasks = int(split[2])
        rundir = split[4]
        binary_name = split[5].strip()
        binaryrelpath = os.readlink(os.path.join(rundir, binary_name))
        paths = []
        for path in [split[7], split[9]]:
            if os.path.isabs(path):
                pass
            else:
                path = os.path.relpath(path, rundir)
            paths.append(path)
        return Run(os.path.dirname(rundir), os.path.basename(rundir),
                   binaryrelpath, stdout=paths[0], stderr=paths[1])

    @classmethod
    def from_dir(cls, dir, tasks=None, **kwargs):
        qualikiz_run = QuaLiKizRun.from_dir(dir, **kwargs)
        parent_dir = os.path.dirname(qualikiz_run.rundir)
        name = os.path.basename(qualikiz_run.rundir)
        return Run(parent_dir, name, qualikiz_run.binaryrelpath, tasks=tasks,
                   stdout=qualikiz_run.stdout, stderr=qualikiz_run.stderr,
                   **kwargs)

    def launch(self):
        self.inputbinaries_exist()
        # Check if batch script is generated
        self.clean()

        cmd = ' '.join(['cd', self.rundir, '&&', self.runstring,
                        '-n', str(self.tasks), './' + os.path.basename(self.binaryrelpath)])
        stdout = open(os.path.join(self.rundir, self.stdout), 'w')
        stderr = open(os.path.join(self.rundir, self.stderr), 'w')
        subprocess.check_call(cmd, shell=True, stdout=stdout, stderr=stderr)


    #def __eq__(self, other):
    #    if isinstance(other, self.__class__):
    #        return self.__dict__ == other.__dict__
    #    return NotImplemented

    #def __ne__(self, other):
    #    if isinstance(other, self.__class__):
    #        return not self == other
    #    return NotImplemented
