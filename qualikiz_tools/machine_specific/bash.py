"""
Copyright Dutch Institute for Fundamental Energy Research (2016-2017)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import subprocess
import multiprocessing as mp
import os
import stat
from warnings import warn

from qualikiz_tools.machine_specific.system import Run, Batch
from qualikiz_tools.qualikiz_io.inputfiles import QuaLiKizPlan
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch

def get_num_threads():
    """Returns amount of threads/virtual cores on current system"""
    return mp.cpu_count()

def get_vcores():
    """Get a list of virtual cores from /proc/cpuinfo"""
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

def get_num_cores():
    """Get the amount of physical cores of the current machine"""
    return len(set(get_vcores()))

class Run(Run):
    """ Defines the run command """
    runstring = 'mpirun'
    defaults = {'cores_per_node': get_num_cores(),
                'threads_per_core': 2,
                'HT': False
               }

    def __init__(self, parent_dir, name, binaryrelpath,
                 qualikiz_plan=None, stdout=None, stderr=None,
                 verbose=False, nodes=1, HT=False, tasks=None,
                 **kwargs):
        """ Initializes the Run class

        Args:
            parent_dir:     Directory the run lives in
            name:           Name of the run. Will also be the folder name
            binaryrelpath:  Path of the binary relative to the run dir
        Kwargs:
            qualikiz_plan:  The QuaLiKizPlan instance used to generate input
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

        self.nodes = nodes
        for name in ['HT', 'threads_per_core']:
            if name in self.defaults:
                setattr(self, name, self.defaults[name])
            else:
                setattr(self, name, None)
        if tasks is None:
            ncores = self.defaults['cores_per_node'] * self.nodes
            tasks = self.calculate_tasks(ncores, HT=self.HT, threads_per_core=self.threads_per_core)
        self.tasks = tasks

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
                           '-n'     , str(self.tasks) ,
                           '-wdir'  , os.path.normpath(os.path.relpath(self.rundir, batch_dir)),
                                      './' + os.path.basename(self.binaryrelpath)])
        if self.stdout != 'STDOUT':
            string += ' > ' + paths[0]
        if self.stderr != 'STDERR':
            string += ' 2> ' + paths[1]
        return string

    @classmethod
    def from_batch_string(cls, string, batchdir):
        """ Reconstruct the Run from a batch string

        Reverse of to_batch_string. Used to reconstruct the run from a batch script.

        Args:
            string:     The string to parse
            batchdir:   The directory of the containing batch script

        Returns:
            The reconstructed Run instance
        """
        split = string.split(' ')
        dict_ = {}

        tasks = int(split[2])
        rundir = os.path.join(batchdir, split[4])
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
                    path = os.path.relpath(os.path.join(batchdir, path), rundir)
            paths.append(path)
        return cls.from_dir(rundir,
                   stdout=paths[0], stderr=paths[1])

    @classmethod
    def from_dir(cls, dir, **kwargs):
        stdout = kwargs.pop('stdout', None)
        stderr = kwargs.pop('stderr', None)
        parameterspath = os.path.join(dir, cls.parameterspath)
        qualikiz_run = QuaLiKizRun.from_dir(dir, stdout=stdout, stderr=stderr, **kwargs)
        parent_dir = os.path.dirname(qualikiz_run.rundir)
        name = os.path.basename(qualikiz_run.rundir)
        if qualikiz_run.stdout == QuaLiKizRun.default_stdout:
            qualikiz_run.stdout = None
        if qualikiz_run.stderr == QuaLiKizRun.default_stderr:
            qualikiz_run.stderr = None
        return cls(parent_dir, name, qualikiz_run.binaryrelpath,
                   stdout=qualikiz_run.stdout, stderr=qualikiz_run.stderr, qualikiz_plan=qualikiz_run.qualikiz_plan, labellist=qualikiz_run.labellist,
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

    def __init__(self, parent_dir, name, runlist,
                 stdout=None, stderr=None,
                 style='sequential',
                 verbose=False):
        """ Initialize batch job

        Args:
            parent_dir:     Directory the batch lives in
            name:           Name of the batch. Will also be the folder name
            runlist:        List of runs contained in this batch

        Kwargs:
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

    def to_batch_file(self, path, overwrite_batch_script=False):
        """ Writes batch script to file

        Args:
            path:       Path of the sbatch script file.
        """
        if overwrite_batch_script:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

        batch_lines = ['#!' + self.shell + '\n\n']

        # Write sruns to file
        batch_lines.append('export OMP_NUM_THREADS=2\n\n')
        batch_lines.append('echo "Starting job {:d}/{:d}"\n'.format(1, len(self.runlist)))
        batch_lines.append(self.runlist[0].to_batch_string(os.path.dirname(path)))
        for ii, run in enumerate(self.runlist[1:]):
            batch_lines.append(' &&\necho "Starting job {:d}/{:d}"'.format(ii + 2, len(self.runlist)))
            batch_lines.append(' &&\n' + run.to_batch_string(os.path.dirname(path)))

        if overwrite_batch_script:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

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
            runlist.append(Run.from_batch_string(run_string, os.path.join(parent_dir, name)))
        batch = Batch(parent_dir, name, runlist, **kwargs)

        return batch

    @classmethod
    def from_dir(cls, dir, *args, **kwargs):
        return cls.from_subdirs(dir, *args, **kwargs)

    def launch(self):
        """ Launch QuaLiKizBatch using a batch script with mpirun
        """
        dirname = os.path.basename(os.path.abspath(os.curdir))
        if self.name != dirname:
            warn("Warning! Launching from outside the batch folder! Experimental!")
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
