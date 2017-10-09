"""
Copyright Dutch Institute for Fundamental Energy Research (2016)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
from warnings import warn
import os
from .system import System
from ..qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch
import multiprocessing as mp
cores_per_node = 24
vcores_per_task = None


class Batch(System.Batch):
    """ Defines a batch job

    This class uses the OpenMP/MPI parameters as defined by Edison,
    but could in principle be extented to support more machines.

    Class Variables:
        - attr:             All possible attributes as defined by Edison
        - sbatch:           Names of attributes as they are in the sbatch file
        - shell:            The shell to use for sbatch scripts. Usually bash
    """
    # pylint: disable=too-many-instance-attributes
    attr = ['nodes',
            'maxtime',
            'partition',
            'tasks_per_node',
            'vcores_per_task',
            'filesystem',
            'name',
            'repo',
            'stderr',
            'stdout',
            'qos']
    sbatch = ['nodes',
              'time',
              'partition',
              'ntasks-per-node',
              'cpus-per-task',
              'license',
              'job-name',
              'account',
              'error',
              'output',
              'qos']
    shell = '/bin/bash'

    def __init__(self, qualikiz_batch, run_instances, name, tasks, maxtime,
                 stdout=None, stderr=None,
                 filesystem='SCRATCH', partition='regular',
                 qos='normal', repo=None, HT=True,
                 vcores_per_task=2,
                 safetytime=1.5, style='sequential'):
        """ Initialize Edison batch job

        Arguments:
            - srun_instances: List of Srun instances included in the Sbatch job
            - name:           Name of the Sbatch job
            - tasks:          Amount of MPI tasks
            - maxtime:        Maximum walltime needed
            - ncpu:      Amount of cpus to be used

        Keyword Arguments:
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

        self.filesystem = filesystem
        if HT:
            vcores_per_core = 2  # Per definition
        else:
            vcores_per_core = 1
        # HT 48 or no HT 24
        self.vcores_per_node = cores_per_node * vcores_per_core
        self.vcores_per_task = vcores_per_task  # 2, as per QuaLiKiz
        self.tasks_per_node = int(self.vcores_per_node / self.vcores_per_task)

        nodes, remainder = divmod(tasks, self.tasks_per_node)
        self.nodes = int(nodes)
        if remainder != 0:
            self.nodes += 1
            warn(str(tasks) + ' tasks not evenly divisible over ' +
                 str(self.tasks_per_node) + ' tasks per node. Using ' +
                 str(self.nodes) + ' nodes.')

        self.repo = repo
        self.qos = qos
        self.maxtime = maxtime
        self.partition = partition
        self.name = name
        self.run_instances = run_instances
        self.stdout = stdout
        self.stderr = stderr

        if style == 'sequential':
            totwallsec = 0.
            tottasks = 0
            runclasslist = []
            for run in self.run_instances:
                totwallsec += run.qualikiz_run.estimate_walltime(ncpu)
                tasks = run.qualikiz_run.calculate_tasks(ncpu, HT=HT)
                tottasks += tasks
            totwallsec *= safetytime
            m, s = divmod(totwallsec, 60)
            h, m = divmod((m + 1), 60)

            # TODO: generalize for non-edison machines
            if partition == 'debug' and (h >= 1 or m >= 30):
                warn('Walltime requested too high for debug partition')
            self.maxtime = ("%d:%02d:%02d" % (h, m, s))
        else:
            raise NotImplementedError('Style {!s} not implemented yet.'.format(style))

    def to_file(self, path):
        """ Writes sbatch script to file

        Arguments:
            - path: Path of the sbatch script file.
        """
        sbatch_lines = ['#!' + self.shell + ' -l\n']
        for attr, sbatch in zip(self.attr, self.sbatch):
            value = getattr(self, attr)
            if value is not None:
                line = '#SBATCH --' + sbatch + '=' + str(value) + '\n'
                sbatch_lines.append(line)

        sbatch_lines.append('\nexport OMP_NUM_THREADS=' +
                            str(self.vcores_per_task) + '\n')

        # Write sruns to file
        for run_instance in self.srun_instances:
            sbatch_lines.append('\n' + run_instance.to_string())
        sbatch_lines.append('\n')

        with open(path, 'w') as file:
            file.writelines(sbatch_lines)

    @classmethod
    def from_file(cls, path):
        """ Reconstruct sbatch from sbatch file """
        new = Sbatch.__new__(cls)
        with open(path, 'r') as file:
            for line in file:
                if line.startswith('#SBATCH --'):
                    line = line.lstrip('#SBATCH --')
                    name, value = line.split('=')
                    value = str_to_number(value.strip())
                    if name in cls.sbatch:
                        setattr(new, cls.attr[cls.sbatch.index(name)], value)
                if line.startswith('srun'):
                    srun_strings.append(line)

        try:
            getattr(new, 'repo')
        except AttributeError:
            setattr(new, 'repo', None)

        new.vcores_per_node = new.tasks_per_node * new.vcores_per_task

        new.srun_instances = []
        for srun_string in srun_strings:
            new.srun_instances.append(Srun.from_string(srun_string))
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


class Run(System.Run, QuaLiKizRun):
    """ Defines the srun command """

    def __init__(self, parent_dir, name, binaryrelpath,
                 qualikiz_plan=None, stdout=None, stderr=None, verbose=False,
                 tasks=None, chdir='.', **kwargs):
        """ Initializes the Srun class

        Arguments:
            - binary_name: The name of the binary relative to where
                           the sbatch script will be
            - tasks:       Amount of MPI tasks needed for the job
        Keyword Arguments:
            - chdir:  Dir to change to before running the command
            - stdout: Standard target of redirect of STDOUT
            - stderr: Standard taget of redirect of STDERR
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
        self.chdir = chdir

    def to_batchstring(self, batch_parent_dir='.'):
        """ Create the run string """
        paths = []
        for path in [self.chdir, self.stdout, self.stderr, self.binaryrelpath]:
            if os.path.isabs(path):
                paths.append(path)
            else:
                paths.append(os.path.relpath(path, batch_parent_dir))

        string = ' '.join(['srun'     ,
                           '-n'       , str(self.tasks)  ,
                           '--chdir'  , paths[0]      ,
                           '--output' , paths[1]      ,
                           '--error'  , paths[2]      ,
                                        paths[3]])
        return string

    @classmethod
    def from_batchstring(cls, string):
        """ Reconstruct the Run from a string """
        split = string.split(' ')
        tasks = int(split[2])
        chdir = split[4]
        stdout = split[6]
        stderr = split[8]
        binary_name = split[9].strip()
        paths = []
        for path in [binary_name, stdout, stderr]:
            if os.path.isabs(path):
                paths.append(path)
            else:
                paths.append(os.path.normpath(os.path.relpath(path, chdir)))
        return Run(os.path.abspath(os.path.dirname(chdir)), os.path.basename(chdir),
                   paths[0], stdout=paths[1], stderr=paths[2])

    @classmethod
    def from_dir(cls, dir, **kwargs):
        qualikiz_run = QuaLiKizRun.from_dir(dir, **kwargs)
        parent_dir = os.path.dirname(qualikiz_run.rundir)
        name = os.path.basename(qualikiz_run.rundir)
        return Run(parent_dir, name, qualikiz_run.binaryrelpath, **kwargs)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self == other
        return NotImplemented
