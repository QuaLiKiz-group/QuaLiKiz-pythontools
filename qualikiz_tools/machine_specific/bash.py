"""
Copyright Dutch Institute for Fundamental Energy Research (2016-2017)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
from warnings import warn
import os
import stat
from .system import Run, Batch
from ..qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch
import subprocess
import multiprocessing as mp

def get_num_threads():
    """Returns amount of threads/virtual cores on current system"""
    return mp.cpu_count()

def get_vcores():
    with open('/proc/cpuinfo', 'r') as file_:
        vcores = []
        for line in file_:
            if line.startswith('physical id'):
                phys_id = int(line.split(':')[1])
            if line.startswith('core id'):
                core_id = int(line.split(':')[1])
                vcores.append((phys_id, core_id))
    if len(vcores) != get_num_threads():
        raise Exception('Amount of threads != amount of virtual cores. Probably error in reading /proc/cpuinfo')
    return vcores

class Run(Run):
    """ Defines the run command """
    runstring = 'mpirun'

    def __init__(self, parent_dir, name, binaryrelpath,
                 qualikiz_plan=None, stdout=None, stderr=None,
                 verbose=False, tasks=None, HT=True, **kwargs):
        """ Initializes the Run class

        Args:
            parent_dir:     Directory the run lives in
            name:           Name of the run. Will also be the folder name
            binaryrelpath:  Path of the binary relative to the run dir
        Kwargs:
            qualikiz_plan:  The QuaLiKizPlan instance used to generate input
            tasks:          Amount of MPI tasks needed for the job. Number of
                            virtual cores by default.
            HT:             Use hyperthreading. [Default: True]
            stdout:         Standard target of redirect of STDOUT [default: terminal]
            stderr:         Standard target of redirect of STDERR [default: terminal]
            verbose:        Verbose output while creating the Run [default: False]
            **kwargs:       kwargs past to superclass
        """
        if stdout is None:
            stdout = 'STDOUT'
        if stderr is None:
            stderr = 'STDERR'
        super().__init__(parent_dir, name, binaryrelpath,
                         qualikiz_plan=qualikiz_plan,
                         stdout=stdout, stderr=stderr,
                         verbose=verbose, **kwargs)
        if tasks is None:
            ncpu = mp.cpu_count()
            self.tasks = self.calculate_tasks(ncpu, HT=HT)
        else:
            self.tasks = tasks

    def to_batch_string(self, batch_parent_dir):
        """ Create string to include in batch job

        This string will be used in the batch script file that runs the jobs.

        Args:
            batch_parent_dir: Directory the batch script lives in. Needed to
                              generate the relative paths.
        """
        paths = []
        for path in [self.stdout, self.stderr]:
            if os.path.isabs(path):
                pass
            else:
                path = os.path.normpath(os.path.join(os.path.relpath(self.rundir, batch_parent_dir), path))
            paths.append(path)
        if self.binaryrelpath is None:
            raise FileNotFoundError('No binary rel path specified, could not find link to QuaLiKiz binary in {!s}'.format(self.rundir))

        string = ' '.join([self.runstring ,
                           '-n'     , str(self.tasks) ,
                           '-wdir'  , self.rundir     ,
                                      './' + os.path.basename(self.binaryrelpath)])
        if self.stdout != 'STDOUT':
            string += ' > ' + paths[0]
        if self.stderr != 'STDERR':
            string += ' 2> ' + paths[1]
        return string

    @classmethod
    def from_batch_string(cls, string):
        """ Reconstruct the Run from a batch string

        Reverse of to_batch_string. Used to reconstruct the run from a batch script.

        Args:
            string:     The string to parse

        Returns:
            The reconstructed Run instance
        """
        split = string.split(' ')
        dict_ = {}

        tasks = int(split[2])
        rundir = split[4]
        binary_name = split[5].strip()
        binaryrelpath = os.readlink(os.path.join(rundir, binary_name))
        paths = []
        for path_index in [7, 9]:
            try:
                path = split[path_index]
            except IndexError:
                path = None
            else:
                if not os.path.isabs(path):
                    path = os.path.relpath(path, rundir)
            paths.append(path)
        return Run(os.path.dirname(rundir), os.path.basename(rundir),
                   binaryrelpath, stdout=paths[0], stderr=paths[1])

    @classmethod
    def from_dir(cls, dir, tasks=None, **kwargs):
        stdout = kwargs.pop('stdout', None)
        stderr = kwargs.pop('stderr', None)
        qualikiz_run = QuaLiKizRun.from_dir(dir, stdout=stdout, stderr=stderr, **kwargs)
        parent_dir = os.path.dirname(qualikiz_run.rundir)
        name = os.path.basename(qualikiz_run.rundir)
        if qualikiz_run.stdout == QuaLiKizRun.default_stdout:
            qualikiz_run.stdout = None
        if qualikiz_run.stderr == QuaLiKizRun.default_stderr:
            qualikiz_run.stderr = None
        return Run(parent_dir, name, qualikiz_run.binaryrelpath, tasks=tasks,
                   stdout=qualikiz_run.stdout, stderr=qualikiz_run.stderr,
                   **kwargs)

    def launch(self):
        """ Launch QuaLiKizRun using mpirun

        Special variables self.stdout == 'STDOUT' and self.stderr == 'STDERR'
        will output to terminal.
        """
        self.inputbinaries_exist()
        # Check if batch script is generated
        self.clean()

        cmd = ' '.join(['cd', self.rundir, '&&', self.runstring,
                        '-n', str(self.tasks), './' + os.path.basename(self.binaryrelpath)])
        if self.stdout == 'STDOUT':
            stdout = None
        else:
            stdout = open(os.path.join(self.rundir, self.stdout), 'w')
        if self.stderr == 'STDERR':
            stderr = None
        else:
            stderr = open(os.path.join(self.rundir, self.stderr), 'w')
        subprocess.check_call(cmd, shell=True, stdout=stdout, stderr=stderr)


class Batch(Batch):
    """ Defines a batch job

    Class Variables:
        shell:            The shell to use for batch scripts.
                          Tested only with bash
        run_class:        class that represents the runs contained in batch
    """
    shell = '/bin/bash'
    run_class = Run

    def __init__(self, parent_dir, name, runlist, tasks=None,
                 stdout=None, stderr=None,
                 style='sequential',
                 verbose=False):
        """ Initialize batch job

        Args:
            parent_dir:     Directory the batch lives in
            name:           Name of the batch. Will also be the folder name
            runlist:        List of runs contained in this batch

        Kwargs:
            tasks:          Amount of MPI tasks needed PER RUN. Number of
                            virtual cores by default.
            stdout:         Standard target of redirect of STDOUT [default: terminal]
            stderr:         Standard target of redirect of STDERR [default: terminal]
            style:          How to glue the different runs together. Currently
                            only 'sequential' is used
            verbose:        Verbose output while creating the Run [default: False]
            **kwargs:       kwargs past to superclass

        Kwargs:
            - stdout:     File to write stdout to. By default 'stdout.batch'
            - stderr:     File to write stderr to. By default 'stderr.batch'
        """

        if not all([run.__class__ == self.run_class for run in runlist]):
            raise Exception('Runs are not of class {!s}'.format(self.run_class))
        if stdout is None:
            stdout = 'STDOUT'
        if stderr is None:
            stderr = 'STDERR'
        super().__init__(parent_dir, name, runlist,
                         stdout=stdout, stderr=stderr)

        if style == 'sequential':
            pass
        else:
            raise NotImplementedError('Style {!s} not implemented yet.'.format(style))

    def to_batch_file(self, path):
        """ Writes batch script to file

        Args:
            path:       Path of the sbatch script file.
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
    def from_batch_file(cls, path, **kwargs):
        """ Reconstruct batch from batch file """
        name = os.path.basename(os.path.dirname(path))
        parent_dir = os.path.dirname(os.path.dirname(path))
        run_strings = []
        with open(path, 'r') as file:
            for line in file:
                if line.startswith(Run.runstring):
                    run_strings.append(line)

        runlist = []
        for run_string in run_strings:
            runlist.append(Run.from_batch_string(run_string))
        batch = Batch(parent_dir, name, runlist, **kwargs)

        return batch

    def launch(self):
        """ Launch QuaLiKizBatch using a batch script with mpirun
        """
        dirname = os.path.basename(os.path.abspath(os.curdir))
        if self.name != dirname:
            warn("Warning! Dirname '{!s}' != name of batch '{!s}'. Might lead to unexpected behaviour".format(dirname, self.name))
        self.inputbinaries_exist()
        # Check if batch script is generated
        batchdir = os.path.join(self.parent_dir, self.name)
        script_path = os.path.join(batchdir, self.scriptname)
        if not os.path.exists(script_path):
            warn('Batch script does not exist! Generating.. in {!s}'.format(batchdir))
            self.to_batch_file(os.path.join(script_path))

        self.clean()

        cmd = ' '.join(['cd', batchdir, '&& bash', self.scriptname])
        if self.stdout == 'STDOUT':
            stdout = None
        else:
            stdout = open(os.path.join(batchdir, self.stdout), 'w')
        if self.stderr == 'STDERR':
            stderr = None
        else:
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


    #def __eq__(self, other):
    #    if isinstance(other, self.__class__):
    #        return self.__dict__ == other.__dict__
    #    return NotImplemented

    #def __ne__(self, other):
    #    if isinstance(other, self.__class__):
    #        return not self == other
    #    return NotImplemented
