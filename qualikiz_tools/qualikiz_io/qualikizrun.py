"""
Copyright Dutch Institute for Fundamental Energy Research (2016-2017)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import os
import warnings
from warnings import warn
import shutil
import multiprocessing as mp
from logging import info
from functools import partial

import xarray as xr

from ..qualikiz_io.inputfiles import QuaLiKizPlan
from ..qualikiz_io.outputfiles import (convert_debug, convert_output,
                                       convert_primitive, squeeze_dataset,
                                       orthogonalize_dataset, determine_sizes)
from ..qualikiz_io.outputfiles import (merge_orthogonal, sort_dims)
from .. import netcdf4_engine
from . import __path__ as ROOT
ROOT = ROOT[0]

threads_per_task = 2  # Stuck as per QuaLiKiz code
threads_per_vcore = 1  # Never give one (virtual) CPU more than one task
vcores_per_task = int(threads_per_task / threads_per_vcore)  # == 2

warnings.simplefilter('always', UserWarning)


class PathException(Exception):
    """ Exception thrown when a path should be absolute, but it is not """
    def __init__(self, path):
        message = path + ' must be an absolute path or bad things will happen!'
        super().__init__(message)


class QuaLiKizBatch():
    """ A collection of QuaLiKiz Runs

    This class is used to define a collection of QuaLiKiz Runs. This is more
    or less equivalent with a batch script, but with path awareness and some
    extra smarts built-in.

    Attributes:
        batchinfofile:  The default name of batchinfo file. Used to store
                        batch metadata
        scriptname:     The default name of the sbatch scipt file.
        default_stdout: Default name to write STDOUT to
        default_stderr: Default name to write STDERR to
    """

    batchinfofile = 'batchinfo.json'
    scriptname = 'qualikiz.batch'

    default_stderr = 'stderr.batch'
    default_stdout = 'stdout.batch'

    def __init__(self, parent_dir, name, runlist,
                 stdout=None,
                 stderr=None):
        """ Initialize a batch
        Args:
            parent_dir: Parent directory of the batch directory.
            name:       Name of the batch. This will also be the folder name
            runlist:    A list of QuaLiKizRuns contained in this batch

        Kwargs:
            stdout:     File to write stdout to. By default 'stdout.batch'
            stderr:     File to write stderr to. By default 'stderr.batch'
        """
        self.parent_dir = parent_dir
        self.name = name
        self.runlist = runlist

        if stdout is None:
            self.stdout = QuaLiKizBatch.default_stdout
        else:
            self.stdout = stdout

        if stderr is None:
            self.stderr = QuaLiKizBatch.default_stderr
        else:
            self.stderr = stderr

    def prepare(self, overwrite_batch=None, overwrite_runs=False):
        """ Prepare the batch and runs to be submitted
        This function writes necessary files and folders for the batch
        to run correctly. Note that this does not generate the input files,
        as that might take a while. You can generate those with the
        generate_input function.

        Keyword arguments:
            overwrite_batch: Flag to overwrite the batch folder if it
                               already exists. Prompts the user by default.
            overwrite_runs:  Flag to overwrite the runs folders if they
                               already exist. False by default.
        """
        batchdir = os.path.join(self.parent_dir, self.name)
        batchpath = os.path.join(batchdir, self.scriptname)
        create_folder_prompt(batchdir, overwrite=overwrite_batch)
        self.to_batch_file(batchpath)
        # Create link to python scripts
        for run in self.runlist:
            run.prepare(overwrite=overwrite_runs)

    def generate_input(self, dotprint=False, processes=1, conversion=None):
        """ Generate the input files for all runs

        Keyword arguments:
            dotprint:   Print a dot after each generation. Used for debugging.
            processes:  Amount of processes used to generate. Defaults to 1.
                        Set this to 'max' to autodetect.
            conversion: Function will be called as conversion(input_dir). Can
                        be used to convert input files to older version.
        """
        if processes == 1:
            for run in self.runlist:
                run.generate_input(dotprint=dotprint, conversion=conversion)
        else:
            if processes == 'max':
                tasks = min((mp.cpu_count(), len(self.runlist)))
            else:
                tasks = processes

            pool = mp.Pool(processes=tasks)
            pool.map(partial(QuaLiKizRun.generate_input, dotprint=dotprint, conversion=conversion),
                     self.runlist)

    @classmethod
    def from_dir_recursive(cls, searchdir):
        """ Reconstruct batch from directory tree
        Walks from the given path until it finds a file named
        QuaLiKizBatch.scriptname, and tries to reconstruct the
        batch from there.

        Args:
            searchdir: The path to search

        Returns:
            batchlist: A list of batches found
        """
        batchlist = []
        for (dirpath, __, filenames) in os.walk(searchdir):
            if QuaLiKizBatch.scriptname in filenames:
                batchlist.append(QuaLiKizBatch.from_subdirs(dirpath))
        return batchlist

    @classmethod
    def from_subdirs(cls, batchdir, scriptname=None):
        """ Reconstruct batch from a directory
        This function assumes that the name of the batch can be
        determined by the given batchdir. If the batch was created
        with the functions contained in this module, it should always
        be succesfully re-contructed.

        Args:
            batchdir:   The top directory of the batch

        Kwargs:
            scriptname: name of the script to search for. Defaults to qualikiz.batch.

        Returns:
            qualikizbatch: The reconstructed batch
        """
        batchdir = os.path.realpath(batchdir.rstrip('/'))
        # The name should be the same as the directory name given
        parent_dir, name = os.path.split(batchdir)
        #qualikizbatch = QuaLiKizBatch.__new__(cls)
        #qualikizbatch.parent_dir = os.path.abspath(parent_dir)
        #qualikizbatch.name = name
        if scriptname is None:
            scriptname = cls.scriptname
        batchscript_path = os.path.join(batchdir, scriptname)
        try:
            batch = cls.from_batch_file(batchscript_path)
        except AttributeError:
            warn('No from_file function defined for {!s}, falling back to subdirs'.format(cls))
            runlist = []
        # Try to find the contained runs, they are usually in one of the children
            try:
                runlist = [QuaLiKizRun.from_dir(batchdir)]
            except:
                for subpath in os.listdir(batchdir):
                    if os.path.isdir(subpath):
                        rundir = os.path.join(batchdir, subpath)
                        try:
                            run = QuaLiKizRun.from_dir(rundir)
                        except:
                            pass
                        else:
                            runlist.append(run)
            batch = QuaLiKizBatch(parent_dir, name, runlist)

        return batch

    def to_netcdf(self, runmode='dimx', mode='noglue',
                  genfromtxt=False, encode=None, clean=True,
                  keepfile=True, processes=1):
        """ Convert QuaLiKizBatch output to netcdf

        This function converts the output contained in the output and debug
        folders to netcdf. Optionally the datasets are glued together
        afterwards by setting the 'mode' keyword argument. Compresses
        the dataset by default.

        Kwargs:
            runmode:    Mode to pass to QuaLiKizRun.to_netcdf. Defaults to 'dimx'
            mode:       What to do after netcdfizing runs. 'noglue' by default.abs
                        set 'glue' to glue datasets together
            genfromtxt: Use genfromtxt instead of loadtxt. Slower and loads
                        unreadable values as NaN
            encode:     Default encoding passed to QuaLiKizRun.to_netcdf and
                        to the new dataset. Compresses by default
            clean:      Remove netcdf files generated by QuaLiKizRun.to_netcdf
                        when done. True by default
            keepfile:   Keep read ASCII files. Highy recommended!
            processes:  Amount of processes used to generate. Defaults to 1.
                        Set this to 'max' to autodetect.

        """

        if encode is None:
            encode = {'zlib': True}

        new_netcdf_path = os.path.join(self.parent_dir, self.name, self.name + '.nc')

        # First, look for existing netcdf files
        joblist = [] # jobs that still need to be netcdfized
        for run in self.runlist:
            name = os.path.basename(run.rundir)
            netcdf_path = os.path.join(run.rundir, name + '.nc')
            if not overwrite_prompt(netcdf_path):
                warn('User does not want to overwrite ' + netcdf_path)
            else:
                joblist.append(run.rundir)
        print('Found {:d} jobs'.format(len(joblist)))

        if not overwrite_prompt(new_netcdf_path):
            raise Exception('User does not want to overwrite ' + new_netcdf_path)


        # We want to run one job per core max
        if processes == 'max':
            tasks = min((mp.cpu_count(), len(self.runlist)))

            pool = mp.Pool(processes=tasks)
            pool.map(partial(run_to_netcdf, runmode=runmode, encode=encode,
                             keepfile=keepfile, genfromtxt=genfromtxt), joblist)
        elif processes == 1:
            for job in joblist:
                run_to_netcdf(job, runmode=runmode, encode=encode,
                              genfromtxt=genfromtxt, keepfile=keepfile)
        print('jobs netcdfized')

        # Now we have the hypercubes. Let's find out which dimensions
        # we're missing and glue the datasets together
        newds = None
        if mode == 'glue':
            if len(self.runlist) > 1:
                name = os.path.basename(self.runlist[0].rundir)
                netcdf_path = os.path.join(self.runlist[0].rundir, name + '.nc')
                newds = xr.open_dataset(netcdf_path, engine=netcdf4_engine)
                newds.load()

                print('Merging ' + os.path.join(self.parent_dir, self.name))
                for run in self.runlist[1:]:
                    name = os.path.basename(run.rundir)
                    netcdf_path = os.path.join(run.rundir, name + '.nc')
                    ds = xr.open_dataset(netcdf_path, engine=netcdf4_engine)
                    ds.load()
                    newds = merge_orthogonal([newds, ds])
                    ds.close()

                newds = sort_dims(newds)
                encoding = {}
                for name, __ in newds.items():
                    encoding[name] = {}
                    for enc_name, enc in encode.items():
                        encoding[name][enc_name] = enc
                newds.to_netcdf(new_netcdf_path,
                                engine=netcdf4_engine, format='NETCDF4', encoding=encoding)
                newds.close()
        elif mode == 'noglue':
            pass
        else:
            raise NotImplementedError('Mode ' + mode)

        if clean and newds is not None:
            for run in self.runlist:
                name = os.path.basename(run.rundir)
                netcdf_path = os.path.join(run.rundir, name + '.nc')
                os.remove(netcdf_path)

    def clean(self):
        """ Remove all output """
        for run in self.runlist:
            run.clean()
        batchdir = os.path.join(self.parent_dir, self.name)
        try:
            os.remove(os.path.join(batchdir, self.batchinfofile))
            os.remove(os.path.join(batchdir, self.default_stdout))
            os.remove(os.path.join(batchdir, self.default_stderr))
        except FileNotFoundError:
            pass

    def is_done(self):
        """ Check if job is done running
        Returns:
            True if job is done
        """
        done = True
        for run in self.runlist:
            done &= run.is_done()
        return done

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            attrs = self.__dict__.copy()
            other_attrs = other.__dict__.copy()
            equal = True
            for name in ['stderr', 'stdout']:
                equal = equal and os.path.samefile(attrs.pop(name), other_attrs.pop(name))
            return attrs == other_attrs and equal
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self == other
        return NotImplemented


class QuaLiKizRun:
    """ Defines everything needed for a single run of QuaLiKiz

    Attributes:
        parameterspath: Default path where the parameters json is
        outputdir:      Relative path to the output folder
        primitivedir:   Relative path to the primitive output folder
        debugdir:       Relative path to the debug folder
        inputdir:       Relative path to the input folder
        default_stdout: Default name to write STDOUT to
        default_stderr: Default name to write STDERR to
    """
    parameterspath = 'parameters.json'
    outputdir = 'output'
    primitivedir = 'output/primitive'
    debugdir = 'debug'
    inputdir = 'input'

    default_stderr = 'stderr.run'
    default_stdout = 'stdout.run'

    def __init__(self, parent_dir, name, binaryrelpath,
                 qualikiz_plan=None,
                 stdout=None,
                 stderr=None,
                 verbose=False):
        """ Initialize an empty QuaLiKiz run
        Args:
            parent_dir:    Parent of where the run folder will be.
            name:          The name of the QuaLiKiz Run. This will be the
                           name of the folder that will be generated
            binaryrelpath: The name of the binary that needs to be run.
                           Usually a relative path to the run folder.

        Kwargs:
            qualikiz_plan: The QuaLiKizPlan, usually read from json. Will
                           load the parameter_template by default
            stdout:        Path to the STDOUT file.
            stderr:        Path to the STDERR file.
            verbose:       Print verbose information when initializing.
        """
        self.rundir = os.path.join(parent_dir, name)

        if verbose:
            print('Creating new QuaLiKiz run in {!s}'.format(self.rundir))

        if stdout is None:
            self.stdout = QuaLiKizRun.default_stdout
        else:
            self.stdout = stdout

        if stderr is None:
            self.stderr = QuaLiKizRun.default_stderr
        else:
            self.stderr = stderr

        self.binaryrelpath = binaryrelpath

        # Load the default parameters if no plan is defined
        if qualikiz_plan is None:
            templatepath = os.path.join(ROOT, 'parameters_template.json')
            qualikiz_plan = QuaLiKizPlan.from_json(templatepath)
        self.qualikiz_plan = qualikiz_plan

    def prepare(self, overwrite=None):
        """ Write all Run folders to file
        This will generate a folders for each run. Note that this will not
        generate the input files, just the skeleton needed. For large runs
        the input generation can take a while. Generate input binaries using
        the generate_input function.

        Kwargs:
            overwrite:  Overwrite the directory if it exists. Prompts the
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
        # Create a parameters file
        self.qualikiz_plan.to_json(os.path.join(rundir, self.parameterspath))

    def _create_output_folders(self, path):
        """ Create the output folders """
        os.makedirs(os.path.join(path, self.outputdir), exist_ok=True)
        os.makedirs(os.path.join(path, self.primitivedir), exist_ok=True)
        os.makedirs(os.path.join(path, self.debugdir), exist_ok=True)

    def generate_input(self, dotprint=False, conversion=None):
        """ Generate the input binaries for a QuaLiKiz run

        Kwargs:
            dotprint:   Print a dot after each generation. Used for debugging.
            conversion: Function will be called as conversion(input_dir). Can
                        be used to convert input files to older version.
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

        if conversion is not None:
            conversion(inputdir)

    def inputbinaries_exist(self):
        """ Check if the input binaries exist
        Currently only checks for R0.bin. Change this if the QuaLiKiz
        input files ever change!

        Returns:
            True if the input binaries exist
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

        Returns:
            Estimated walltime in seconds
        """
        cputime = self.estimate_cputime(cores)
        return cputime / cores

    def estimate_cputime(self, cores):
        """ Estimate the cpu time needed to run
        Currently just uses a worst-case assumtion. In reality cpus_per_dimxn
        should depend on the dimxn per core. It also depends on the amount of
        stable points in the run, which is not known a-priori.

        Returns:
            Estimated cputime in seconds
        """
        dimxn = self.qualikiz_plan.calculate_dimxn()
        cpus_per_dimxn = 0.8
        return dimxn * cpus_per_dimxn

    def calculate_tasks(self, cores, HT=True):
        """ Calulate the amount of MPI tasks needed based on the cores used

        Args:
            cores: The amount of cores to use

        Kwargs:
            HT: Flag to use HyperThreading. By default True.

        Returns:
            Tasks to use to run this QuaLiKizRun
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

    @classmethod
    def from_dir(cls, dir, binaryrelpath=None,
                 stdout=default_stdout,
                 stderr=default_stderr):
        """ Reconstruct Run from directory
        Try to reconstruct the Run from a directory. Gives a warning if
        STDOUT and STDERR cannot be found on their given or default location.

        Args:
            dir: Root directory of the Run

        Kwargs:
            binarylinkpath: Path to the link pointing to the QuaLiKiz binary
            stdout:         Where to look for the STDOUT file
            stderr:         Where to look for the STDERR file

        Returns:
            Reconstructed QuaLiKizRun
        """
        rundir = os.path.realpath(dir.rstrip('/'))
        parent_dir, name = os.path.split(rundir)
        parent_dir = os.path.abspath(parent_dir)
        # We assume the binary is named something with 'QuaLiKiz' in it
        if binaryrelpath is None:
            for file in os.listdir(rundir):
                if 'QuaLiKiz' in file:
                    binaryrelpath = os.readlink(os.path.join(rundir, file))
                    break
        if binaryrelpath is None:
            raise Exception('Could not find link to QuaLiKiz binary. Please supply `binaryrelpath`')
        #binarybasepath = os.path.basename(binaryrelpath)
        #binaryrelpath = os.readlink(os.path.join(rundir, binarybasepath))
        planpath = os.path.join(rundir, cls.parameterspath)
        qualikiz_plan = QuaLiKizPlan.from_json(planpath)
        stdout = cls._find_file(stdout, rundir)
        stderr = cls._find_file(stderr, rundir)
        return QuaLiKizRun(parent_dir, name, binaryrelpath,
                           qualikiz_plan=qualikiz_plan,
                           stdout=stdout, stderr=stderr)

    @classmethod
    def _find_file(cls, path, rundir):
        """ Try to find a file. Used for STDOUT and STDERR """
        if not os.path.isfile(path):
            info('Could not find file at \'' + str(path) + '\' searching..')
            path = os.path.join(rundir, os.path.basename(path))
            if not os.path.isfile(path):
                info('Could not find file at \'' + str(path) +
                     '\', file was probably not saved')
                path = None
            else:
                info('Found file at \'' + path + '\'')
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
            attrs = self.__dict__.copy()
            other_attrs = other.__dict__.copy()
            equal = True
            for name in ['binaryrelpath', 'stderr', 'stdout', 'rundir']:
                equal = equal and os.path.samefile(attrs.pop(name), other_attrs.pop(name))
            return attrs == other_attrs and equal
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

    Kwargs:
        overwrite: If None, prompt user. If True, overwrite and if False,
                   throw Exception. None by default

    Returns:
        True if user wants to overwrite
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

    Kwargs:
        overwrite: If None, prompt user. If True, overwrite and if False,
                   throw Exception. None by default
    """
    if overwrite_prompt(path, overwrite=overwrite):
        os.makedirs(path)

def run_to_netcdf(path, runmode='dimx', overwrite=None,
                  genfromtxt=False, keepfile=True, encode=None):
    """ Convert a QuaLiKizRun to netCDF

    Args:
        path:       Path of the run folder to netcdfize. Should contain the debug,
                    output and output/primitive folders.

    Kwargs:
        runmode:       runmode of netcdfizing. If orthogonal, fold the dataset as an
                    hyperrectangle. Any dimx will extract the values
                    in a 1D array.
        overwrite:  Overwrite existing netcdf file. None by default
        genfromtxt: Use genfromtxt instead of loadtxt. Slower and loads
                    unreadable values as nan
        keepfile:   Keep read ASCII files. Highy recommended!
        encode:     Default encoding. This encoding will be added to all
                    variables. Compresses (zlib) by default. See overwrite_prompt.
    """
    if encode is None:
        encode = {'zlib': True}

    name = os.path.basename(path)
    netcdf_path = os.path.join(path, name + '.nc')
    if overwrite_prompt(netcdf_path, overwrite=overwrite):
        sizes = determine_sizes(path, keepfile=keepfile)
        ds = convert_debug(sizes, path, genfromtxt=genfromtxt, keepfile=keepfile)
        ds = convert_output(ds, sizes, path, genfromtxt=genfromtxt, keepfile=keepfile)
        ds = convert_primitive(ds, sizes, path, genfromtxt=genfromtxt, keepfile=keepfile)
        if runmode == 'orthogonal':
            ds = squeeze_dataset(ds)
            ds = orthogonalize_dataset(ds)
        elif runmode == 'dimx':
            pass
        else:
            raise NotImplementedError('Runmode {!s} not implemented'.format(runmode))

        encoding = {}
        # Encode all variables
        for name, __ in ds.items():
            encoding[name] = {}
            for enc_name, enc in encode.items():
                encoding[name][enc_name] = enc
        ds = sort_dims(ds)
        try:
            ds.to_netcdf(netcdf_path, engine='netcdf4',
                         format='NETCDF4', encoding=encoding)
        except ModuleNotFoundError:
            warn('netCDF4 module not found! Please install by `pip install ' +
                 'netcdf4`. Falling back to netCDF3')
            ds.to_netcdf(netcdf_path, encoding=encoding)

def qlk_from_dir(dir):
    if os.path.exists(os.path.join(dir, QuaLiKizBatch.scriptname)):
        dirtype = 'batch'
        qlk_instance = QuaLiKizBatch.from_subdirs(dir)
    elif os.path.exists(os.path.join(dir, QuaLiKizRun.parameterspath)):
        dirtype = 'run'
        qlk_instance = QuaLiKizRun.from_dir(dir)
    else:
        raise Exception('Could not determine folder type')
    return dirtype, qlk_instance
