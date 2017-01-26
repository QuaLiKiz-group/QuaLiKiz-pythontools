"""
Copyright Dutch Institute for Fundamental Energy Research (2016)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import os
import datetime
import subprocess
import warnings
from warnings import warn
from collections import OrderedDict
import math
import shutil
import json
from multiprocessing import Process, Manager
import multiprocessing as mp
import subprocess
import pickle
from qualikiz_tools.qualikiz_io.outputfiles import find_nonmatching_coords, merge_orthogonal, sort_dims
from IPython import embed

threads_per_task = 2  # Stuck as per QuaLiKiz code
threads_per_vcore = 1  # Never give one (virtual) CPU more than one task
vcores_per_task = int(threads_per_task / threads_per_vcore)  # == 2

from ..machine_specific.slurm import Srun, Sbatch
from ..qualikiz_io.inputfiles import QuaLiKizPlan
from ..qualikiz_io.outputfiles import (convert_debug, convert_output,
                                       convert_primitive, squeeze_dataset,
                                       orthogonalize_dataset, determine_sizes)
from .. import netcdf4_engine
from . import __path__ as ROOT

import xarray as xr
from functools import partial
ROOT = ROOT[0]


warnings.simplefilter('always', UserWarning)


class PathException(Exception):
    """ Exception thrown when a path should be absolute, but it is not """
    def __init__(self, path):
        message = path + ' must be an absolute path or bad things will happen!'
        super().__init__(message)


class QuaLiKizBatch:
    """ A collection of QuaLiKiz Runs

    This class is used to define a collection of QuaLiKiz Runs. This is more
    or less equivalent with a batch script, but with path awareness and some
    extra smarts built-in.

    Class variables:
        - batchinfofile: The default name of batchinfo file. Used to store
                         batch metadata
        - scriptname:    The default name of the sbatch scipt file.
    """

    batchinfofile = 'batchinfo.json'
    # TODO: generalize for non-edison machines
    scriptname = 'edison.sbatch'

    # TODO: generalize for non-edison machines
    def __init__(self, batchsdir, name, runlist, ncpu,
                 safetytime=2, style='sequential',
                 stdout=Sbatch.default_stdout,
                 stderr=Sbatch.default_stderr,
                 filesystem='SCRATCH', partition='regular',
                 qos='normal', repo=None, HT=True,
                 vcores_per_task=vcores_per_task):
        """ Initialize a batch
        Arguments:
            - batchsdir: Parent directory of the batch directory.
            - name:      Name of the batch. This will also be the folder name
            - runlist:   A list of QuaLiKizRuns contained in this batch
            - ncpu:      Amount of cpus to be used

        Keyword arguments:
            - safetytime: An extra factor that will be used in the calculation
                          of requested runtime. 1.5x by default
            - style:      How to glue the different runs together. Currently
                          only 'sequential' is used
            - stdout:     Standard target of redirect of STDOUT
            - stderr:     Standard taget of redirect of STDERR
            - filesystem: SLURM filesystem to be used. SCRATCH by default
            - partition:  Which Edison partition to use. 'regular' by default
            - qos:        SLURM qos to be used. normal by default
            - HT:         Use hyperthreading. True by default
        """
        # To be always sure to find the dir, this needs to be absolute
        if os.path.isabs(batchsdir):
            self.batchsdir = batchsdir
        else:
            raise PathException('batchdir')
        self.name = name

        self.runlist = runlist
        # TODO: generalize for non-edison machines
        self.batch = self.generate_batchscript(ncpu,
                                               safetytime=safetytime,
                                               style=style,
                                               stdout=stdout, stderr=stderr,
                                               filesystem=filesystem,
                                               partition=partition,
                                               repo=repo,
                                               qos=qos,
                                               HT=HT)

    def prepare(self, overwrite_batch=None, overwrite_runs=False):
        """ Prepare the batch and runs to be submitted
        This function writes necessary files and folders for the batch
        to run correctly. Note that this does not generate the input files,
        as that might take a while. You can generate those with the
        generate_input function.

        Keyword arguments:
            - overwrite_batch: Flag to overwrite the batch folder if it
                               already exists. Prompts the user by default.
            - overwrite_runs:  Flag to overwrite the runs folders if they
                               already exist. False by default.
        """
        batchdir = os.path.join(self.batchsdir, self.name)
        batchpath = os.path.join(batchdir, self.scriptname)
        create_folder_prompt(batchdir, overwrite=overwrite_batch)
        self.batch.to_file(batchpath)
        # Create link to python scripts
        os.symlink(QuaLiKizRun.pythondir,
                   os.path.join(batchdir, QuaLiKizRun.pythonreldir))
        # Create link to run script
        os.symlink(os.path.join(QuaLiKizRun.pythondir, 'qualikiz_io/run.py'),
                   os.path.join(batchdir, 'run.py'))
        for run in self.runlist:
            run.prepare(overwrite=overwrite_runs)

    def generate_input(self, dotprint=False):
        """ Generate the input files for all runs

        Keyword arguments:
            - dotprint: Print a dot after each generation. Used for debugging.
        """
        tasks = min((mp.cpu_count(), len(self.runlist)))

        pool = mp.Pool(processes=tasks)
        pool.map(QuaLiKizRun.generate_input, self.runlist)

    # TODO: generalize for non-edison machines
    def generate_batchscript(self, ncpu,
                             safetytime=1.5, style='sequential',
                             stdout=Sbatch.default_stdout,
                             stderr=Sbatch.default_stderr,
                             filesystem='SCRATCH', partition='regular',
                             qos='normal', repo=None, HT=True,
                             vcores_per_task=vcores_per_task):
        """ Generate the batch script
        Currently only supports edison-style run scripts.

        Arguments:
            - ncpu:      Amount of cpus to be used

        Keyword arguments:
            - safetytime: An extra factor that will be used in the calculation
                          of requested runtime. 1.5x by default
            - style:      How to glue the different runs together. Currently
                          only 'sequential' is used
            - stdout:     Standard target of redirect of STDOUT
            - stderr:     Standard taget of redirect of STDERR
            - filesystem: SLURM filesystem to be used. SCRATCH by default
            - partition:  Which Edison partition to use. 'regular' by default
            - qos:        SLURM qos to be used. normal by default
            - repo:       Repository used to bill hours. None by default.
            - HT:         Use hyperthreading. True by default

        Returns:
            - batch:      The batch script
        """
        if style == 'sequential':
            totwallsec = 0.
            tottasks = 0
            runclasslist = []
            for run in self.runlist:
                totwallsec += run.estimate_walltime(ncpu)
                tasks = run.calculate_tasks(ncpu, HT=HT)
                tottasks += tasks
                runclass = run.generate_runclass(tasks)
                runclasslist.append(runclass)
            totwallsec *= safetytime
            m, s = divmod(totwallsec, 60)
            h, m = divmod((m + 1), 60)

            # TODO: generalize for non-edison machines
            if partition == 'debug' and (h >= 1 or m >= 30):
                warn('Walltime requested too high for debug partition')
            maxtime = ("%d:%02d:%02d" % (h, m, s))

            # TODO: generalize for non-edison machines
            batch = Sbatch(runclasslist, self.name, tasks, maxtime,
                           stdout=stdout, stderr=stderr,
                           filesystem=filesystem, partition=partition,
                           qos=qos, repo=repo, HT=HT,
                           vcores_per_task=vcores_per_task)
        return batch

    @classmethod
    def from_dir_recursive(cls, searchdir):
        """ Reconstruct batch from directory tree
        Walks from the given path until it finds a file named
        QuaLiKizBatch.scriptname, and tries to reconstruct the
        batch from there.

        Arguments:
            - searchdir: The path to search

        Returns:
            - batchlist: A list of batches found
        """
        batchlist = []
        for (dirpath, dirnames, filenames) in os.walk(searchdir):
            if QuaLiKizBatch.scriptname in filenames:
                batchlist.append(QuaLiKizBatch.from_dir(dirpath))
        return batchlist

    @classmethod
    def from_dir(cls, batchdir):
        """ Reconstruct batch from a directory
        This function assumes that the name of the batch can be
        determined by the given batchdir. If the batch was created
        with the functions contained in this module, it should always
        be succesfully re-contructed.


        Arguments:
            - batchdir: The top directory of the batch

        Returns:
            - qualikizbatch: The reconstructed batch
        """
        batchdir = os.path.realpath(batchdir.rstrip('/'))
        # The name should be the same as the directory name given
        batchsdir, name = os.path.split(batchdir)
        qualikizbatch = QuaLiKizBatch.__new__(cls)
        qualikizbatch.batchsdir = os.path.abspath(batchsdir)
        qualikizbatch.name = name
        batchdir = os.path.join(batchsdir, name)
        batchpath = os.path.join(batchdir, cls.scriptname)
        qualikizbatch.batch = Sbatch.from_file(batchpath)

        qualikizbatch.runlist = []
        # Try to find the contained runs. If they can't be found at the path
        # in the batch script, they are usually in one of the children
        for srun_instance in qualikizbatch.batch.srun_instances:
            rundir = srun_instance.chdir
            if not os.path.isdir(rundir):
                warn('Your batch script will not work!')
                warn('Could not find run at \'' +
                     str(rundir) + '\' searching..')
                rundir = os.path.join(batchdir, os.path.basename(rundir))
                rundir = os.path.abspath(rundir)
                if not os.path.isdir(rundir):
                    warn('Could not find run at \'' +
                         str(rundir) + '\' searching..')
                    rundir = os.path.join(batchsdir, os.path.basename(rundir))
                    rundir = os.path.abspath(rundir)
                    if not os.path.isdir(rundir):
                        raise Exception('Could not find run')
                    else:
                        warn('Found run at \'' + rundir + '\'')
                else:
                    warn('Found run at \'' + rundir + '\'')

            run = QuaLiKizRun.from_dir(rundir, srun_instance.binary_name,
                                       stdout=srun_instance.stdout,
                                       stderr=srun_instance.stderr)
            qualikizbatch.runlist.append(run)

        return qualikizbatch

    def queue_batch(self):
        """ Queue the batch
        Queues the batch. Has some sanity checks to check if the run will
        be succesful. Also dumps some run information to file that can be
        used to profile the runs.
        """
        # Check if the input binaries are generated
        for run in self.runlist:
            run.inputbinaries_exist()
        # Check if batch script is generated
        batchdir = os.path.join(self.batchsdir, self.name)
        batchpath = os.path.join(batchdir, self.scriptname)
        if not os.path.exists(batchpath):
            raise Exception('batch script does not exist!')

        # TODO: generalize for non-edison machines
        cmd = 'sbatch --workdir=' + os.getcwd() + ' ' + batchpath
        output = subprocess.check_output(cmd, shell=True)
        batchinfo['jobnumber'] = output.split()[-1].decode('utf-8')
        batchinfo['submittime'] = datetime.datetime.now()

        print('Queued batch with jobnumber ' + str(batchinfo['jobnumber']))

        # Dump some important profiling stuff to file
        batchinfopath = os.path.join(batchdir, QuaLiKizBatch.batchinfofile)
        with open(batchinfopath, 'w') as file_:
            # Some magic to correctly handle date/time info
            json.dump(batchinfo, file_, default=self.dthandler)
        return batchinfo['jobnumber']

    def dthandler(self, obj):
        if isinstance(obj, datetime.datetime):
            obj.isoformat()
        else:
            json.JSONEncoder().default(obj)

    def to_netcdf(self, runmode='orthogonal', mode='glue', overwrite=None,
                  genfromtxt=False, encode={'zlib': True}, clean=True):
        """ Convert QuaLiKizBatch output to netcdf

        This function converts the output contained in the output and debug
        folders to netcdf. Optionally the datasets are glued together
        afterwards by setting the 'mode' keyword argument. Compresses
        the dataset by default.

        Keyword Arguments:
            runmode:   Mode to pass to QuaLiKizRun.to_netcdf
            mode:      What to do after netcdfizing runs. 'glue' by default; glue
                       datasets together
            overwrite: Overwrite existing netcdf file? Ask user by default
            genfromtxt: Use genfromtxt instead of loadtxt. Slower and loads
                        unreadable values as nan
            encode:    Default encoding passed to QuaLiKizRun.to_netcdf and
                       to the new dataset. Compresses by default
            clean:     Remove netcdf files generated by QuaLiKizRun.to_netcdf
                       when done. True by default
        """

        new_netcdf_path = os.path.join(self.batchsdir, self.name, self.name + '.nc')

        # First, look for existing netcdf files
        joblist = [] # jobs that still need to be netcdfized
        for run in self.runlist:
            name = os.path.basename(run.rundir)
            netcdf_path = os.path.join(run.rundir, name + '.nc')
            if not overwrite_prompt(netcdf_path):
                warn('User does not want to overwrite ' + netcdf_path)
            else:
                joblist.append(run.rundir)

        if not overwrite_prompt(new_netcdf_path):
            raise Exception('User does not want to overwrite ' + new_netcdf_path)


        # We want to run one job per core max
        tasks = min((mp.cpu_count(), len(self.runlist)))
        
        pool = mp.Pool(processes=tasks)
        pool.map(partial(run_to_netcdf, mode=runmode, encode=encode,
                         genfromtxt=genfromtxt), joblist)
        print('jobs netcdfized')

        # Now we have the hypercubes. Let's find out which dimensions
        # we're missing and glue the datasets together
        if mode == 'glue':
            dss = []
            name = os.path.basename(self.runlist[0].rundir)
            netcdf_path = os.path.join(self.runlist[0].rundir, name + '.nc')
            newds = xr.open_dataset(netcdf_path, engine=netcdf4_engine)
            newds.load()

            print('Merging ' + os.path.join(self.batchsdir, self.name))
            for run in self.runlist[1:]:
                name = os.path.basename(run.rundir)
                netcdf_path = os.path.join(run.rundir, name + '.nc')
                ds = xr.open_dataset(netcdf_path, engine=netcdf4_engine)
                ds.load()
                newds = merge_orthogonal([newds, ds])
                ds.close()

            newds = sort_dims(newds)
            encoding = {}
            for name, array in newds.items():
                encoding[name] = {}
                for enc_name, enc in encode.items():
                    encoding[name][enc_name] = enc
            newds.to_netcdf(new_netcdf_path, engine=netcdf4_engine, format='NETCDF4', encoding=encoding)
            newds.close()
        elif mode == 'noglue':
            pass
        else:
            raise NotImplementedError('Mode ' + mode)

        if clean:
            for run in self.runlist:
                name = os.path.basename(run.rundir)
                netcdf_path = os.path.join(run.rundir, name + '.nc')
                os.remove(netcdf_path)

    def clean(self):
        """ Remove all output """
        for run in self.runlist:
            run.clean()
        batchdir = os.path.join(self.batchsdir, self.name)
        try:
            os.remove(os.path.join(batchdir, QuaLiKizBatch.batchinfofile))
            os.remove(os.path.join(batchdir, Sbatch.default_stdout))
            os.remove(os.path.join(batchdir, Sbatch.default_stderr))
        except FileNotFoundError:
            pass

    def is_done(self):
        """ Check if job is done running """
        done = True
        for run in self.runlist:
            done &= run.is_done()
        return done

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self == other
        return NotImplemented


class QuaLiKizRun:
    """ Defines everything needed for a single run of QuaLiKiz

    Class variables:
        - parameterspath: Default path where the parameters json is
        - pythonreldir:   Default name of link to the python module
        - pythondir:      Absolute path to the python module
        - outputdir:      Relative path to the output folder
        - primitivedir:   Relative path to the primitive output folder
        - debugdir:       Relative path to the debug folder
        - inputdir:       Relative path to the input folder
    """
    parameterspath = 'parameters.json'
    pythondir = os.path.realpath(os.path.dirname(ROOT))
    pythonreldir = os.path.basename(pythondir)
    outputdir = 'output'
    primitivedir = 'output/primitive'
    debugdir = 'debug'
    inputdir = 'input'

    def __init__(self, runsdir, name, binaryrelpath, qualikiz_plan=None,
                 stdout=Srun.default_stdout,
                 stderr=Srun.default_stderr):
        """ Initialize an empty QuaLiKiz run
        Arguments:
            - runsdir:       Parent of where the run folder will be. Should
                             be an absolute path
            - name:          The name of the QuaLiKiz Run. This will be the
                             name of the folder that will be generated
            - binaryrelpath: The name of the binary that needs to be run.
                             Usually a relative path to the run folder.

        Keyword arguments:
            - qualikiz_plan: The QuaLiKizPlan, usually read from json. Will
                             load the parameter_template by default
            - stdout:        Path to the STDOUT file.
            - stderr:        Path to the STDERR file.
        """
        # Rundir should be an absolute path
        if os.path.isabs(runsdir):
            self.rundir = os.path.join(runsdir, name)
        else:
            raise PathException('runsdir')

        # Set the STDERR and STDOUT of the run
        if not os.path.isabs(stdout):
            stdout = os.path.abspath(os.path.join(self.rundir, stdout))
        self.stdout = stdout
        if not os.path.isabs(stderr):
            stderr = os.path.abspath(os.path.join(self.rundir, stderr))
        self.stderr = stderr

        self.binaryrelpath = binaryrelpath
        # Load the default parameters if no plan is defined
        if qualikiz_plan is None:
            templatepath = os.path.join(self.pythondir,
                                        'qualikiz_io/parameters_template.json')
            qualikiz_plan = QuaLiKizPlan.from_json(templatepath)
        self.qualikiz_plan = qualikiz_plan

    def prepare(self, overwrite=None):
        """ Write all Run folders to file
        This will generate a folders for each run. Note that this will not
        generate the input files, just the skeleton needed. For large runs
        the input generation can take a while. Generate input binaries using
        the generate_input function.

        Keyword Arguments:
            - overwrite:  Overwrite the directory if it exists. Prompts the
                          user by default.
        """

        rundir = self.rundir

        create_folder_prompt(rundir, overwrite=overwrite)

        self._create_output_folders(rundir)
        os.makedirs(os.path.join(rundir, self.inputdir), exist_ok=True)
        # Check if the binary we are trying to link to exists
        absbindir = os.path.join(rundir, self.binaryrelpath)
        if not os.path.exists(absbindir):
            warn('Warning! Binary at ' + absbindir + ' does not ' +
                 'exist! Run will fail!')
        # Create link to binary
        binarybasepath = os.path.basename(self.binaryrelpath)
        os.symlink(self.binaryrelpath,
                   os.path.join(rundir, binarybasepath))
        # Create link to python scripts
        if not os.path.exists(os.path.join(rundir, self.pythonreldir)):
            os.symlink(self.pythondir,
                       os.path.join(rundir, self.pythonreldir))
        # Create a parameters file
        self.qualikiz_plan.to_json(os.path.join(rundir, self.parameterspath))

    def _create_output_folders(self, path):
        """ Create the output folders """
        os.makedirs(os.path.join(path, self.outputdir), exist_ok=True)
        os.makedirs(os.path.join(path, self.primitivedir), exist_ok=True)
        os.makedirs(os.path.join(path, self.debugdir), exist_ok=True)

    def generate_input(self, dotprint=False):
        """ Generate the input binaries for a QuaLiKiz run

        Keyword arguments:
            - dotprint: Print a dot after each generation. Used for debugging.
        """
        parameterspath = os.path.join(self.rundir, 'parameters.json')

        plan = QuaLiKizPlan.from_json(parameterspath)
        input_binaries = plan.setup()
        inputdir = os.path.join(self.rundir, self.inputdir)

        if dotprint:
            print('.', end='', flush=True)
        os.makedirs(inputdir, exist_ok=True)
        for name, value in input_binaries.items():
            with open(os.path.join(inputdir, name + '.bin'), 'wb') as file_:
                value.tofile(file_)

    def inputbinaries_exist(self):
        """ Check if the input binaries exist
        Currently only checks for R0.bin. Change this if the QuaLiKiz
        input files ever change!
        """
        input_binary = os.path.join(self.rundir, self.inputdir, 'R0.bin')
        exist = True
        if not os.path.exists(input_binary):
            warn('Warning! Input binary at ' + input_binary + ' does not ' +
                 'exist! Run will fail! Please generate input binaries!')
            exist = False
        return exist

    def estimate_walltime(self, cores):
        """ Estimate the walltime needed to run
        This directely depends on the CPU time needed and cores needed to run.
        Currently uses worst-case estimate.
        """
        cputime = self.estimate_cputime(cores)
        return cputime / cores

    def estimate_cputime(self, cores):
        """ Estimate the cpu time needed to run
        Currently just uses a worst-case assumtion. In reality cpus_per_dimxn
        should depend on the dimxn per core.
        """
        dimxn = self.qualikiz_plan.calculate_dimxn()
        cpus_per_dimxn = 0.8
        return dimxn * cpus_per_dimxn

    def calculate_tasks(self, cores, HT=True):
        """ Calulate the amount of MPI tasks needed based on the cores used

        Arguments:
            - cores: The amount of cores to use

        Keyword Arguments:
            - HT: Flag to use HyperThreading. By default True.
        """
        if HT:
            vcores_per_core = 2  # Per definition
        else:
            vcores_per_core = 1

        cores_per_task = int(vcores_per_task / vcores_per_core)  # HT 1, !HT 2
        tasks, remainder = divmod(cores, cores_per_task)
        tasks = int(tasks)
        if remainder != 0:
            warn(str(cores) + ' cores not evenly divisible over ' +
                 str(cores_per_task) + ' cores per task. Using ' +
                 str(tasks) + ' tasks.')
        return tasks

    def generate_runclass(self, tasks):
        """ Generates the class of the run. Edison only """
        srun = Srun(self.binaryrelpath, tasks, chdir=self.rundir,
                    stdout=self.stdout, stderr=self.stderr)
        return srun

    @classmethod
    def from_dir(cls, dir, binaryrelpath,
                 stdout=Srun.default_stdout,
                 stderr=Srun.default_stderr):
        """ Reconstruct Run from directory
        Try to reconstruct the Run from a directory. Gives a warning if
        STDOUT and STDERR cannot be found on their given or default location.

        Arguments:
            - dir: Root directory of the Run
            - binaryrelpath: Path to the binary that should be used in the Run

        Keyword arguments:
            - stdout: Where to look for the STDOUT file
            - stderr: Where to look for the STDERR file
        """
        rundir = os.path.realpath(dir.rstrip('/'))
        runsdir, name = os.path.split(rundir)
        runsdir = os.path.abspath(runsdir)
        binarybasepath = os.path.basename(binaryrelpath)
        binaryrelpath = os.readlink(os.path.join(rundir, binarybasepath))
        planpath = os.path.join(rundir, cls.parameterspath)
        qualikiz_plan = QuaLiKizPlan.from_json(planpath)
        stdout = cls._find_file(stdout, rundir)
        stderr = cls._find_file(stderr, rundir)
        return QuaLiKizRun(runsdir, name, binaryrelpath,
                           qualikiz_plan=qualikiz_plan,
                           stdout=stdout, stderr=stderr)

    @classmethod
    def _find_file(cls, path, rundir):
        """ Try to find a file. Used for STDOUT and STDERR """
        if not os.path.isfile(path):
            warn('Could not find file at \'' + str(path) + '\' searching..')
            path = os.path.join(rundir, os.path.basename(path))
            if not os.path.isfile(path):
                warn('Could not find file at \'' + str(path) +
                     '\', file was probably not saved')
            else:
                warn('Found file at \'' + path + '\'')
        return path


    def clean(self):
        """ Cleans run folder to state before it was run """
        try:
            suffix = '.dat'
            self._clean_suffix(os.path.join(self.rundir, self.outputdir),
                               suffix)
            self._clean_suffix(os.path.join(self.rundir, self.primitivedir),
                               suffix)
            self._clean_suffix(os.path.join(self.rundir, self.debugdir),
                               suffix)
            os.remove(os.path.join(self.rundir, self.stdout))
            os.remove(os.path.join(self.rundir, self.stderr))
        except FileNotFoundError:
            pass

    @classmethod
    def _clean_suffix(cls, dir, suffix):
        """ Removes all files with suffix in dir """
        for file in os.listdir(dir):
            if file.endswith(suffix):
                os.remove(os.path.join(dir, file))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self == other
        return NotImplemented

    def to_netcdf(self, **kwargs):
        """ Convert the output and debug to netCDF """
        run_to_netcdf(self.rundir, **kwargs)

    def is_done(self):
        last_output = os.path.join(self.rundir, 'output/vfi_GB.dat')
        return os.path.isfile(last_output)


def overwrite_prompt(path, overwrite=None):
    """ Prompt user if file/path can be overwritten

    Keyword Arguments:
        overwrite: If None, prompt user. If True, overwrite and if False,
                   throw Exception. None by default
    """
    if os.path.isfile(path) or os.path.isdir(path):
        if overwrite is None:
            resp = input('path exists, overwrite? [Y/n]')
            if resp == '' or resp == 'Y' or resp == 'y':
                overwrite = True
            else:
                overwrite = False
        if overwrite:
            print('overwriting')
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    else:
        overwrite = True
    return overwrite

def create_folder_prompt(path, overwrite=None):
    """ Overwrite folder prompt

    Keyword Arguments:
        overwrite: If None, prompt user. If True, overwrite and if False,
                   throw Exception. None by default
    """
    if overwrite_prompt(path, overwrite=overwrite):
        os.makedirs(path)

def run_to_netcdf(path, mode='orthogonal', overwrite=None,
                  genfromtxt=False, encode={'zlib': True}):
    """ Convert a QuaLiKizRun to netCDF

    Arguments:
        path: Path of the run folder to netcdfize. Should contain the debug,
              output and output/primitive folders.

    Keyword Arguments:
        mode:      Mode of netcdfizing. If orthogonal, fold the dataset as an
                   hyperrectangle. Any other value will just extract the values
                   in a 1D array.
        overwrite: Overwrite existing netcdf file. None by default
        genfromtxt: Use genfromtxt instead of loadtxt. Slower and loads
                    unreadable values as nan
        encode:    Default encoding. This encoding will be added to all
                   variables. Compresses (zlib) by default. See overwrite_prompt.
    """
    name = os.path.basename(path)
    netcdf_path = os.path.join(path, name + '.nc')
    if overwrite_prompt(netcdf_path, overwrite=overwrite):
        sizes = determine_sizes(path)
        ds = convert_debug(sizes, path, genfromtxt=genfromtxt)
        ds = convert_output(ds, sizes, path, genfromtxt=genfromtxt)
        ds = convert_primitive(ds, sizes, path, genfromtxt=genfromtxt)
        if mode == 'orthogonal':
            ds = squeeze_dataset(ds)
            ds = orthogonalize_dataset(ds)

        encoding = {}
        # Encode all variables
        for name, array in ds.items():
            encoding[name] = {}
            for enc_name, enc in encode.items():
                encoding[name][enc_name] = enc
        ds = sort_dims(ds)
        ds.to_netcdf(netcdf_path, engine='netcdf4',
                     format='NETCDF4', encoding=encoding)
