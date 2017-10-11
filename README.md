# QuaLiKiz-pythontools

*A collection of tools for QuaLiKiz in Python.*

## Purpose

This is a collection of Python modules to be used for working with QuaLiKiz,
a quasi-linear gyrokinetic code. QuaLiKiz can be found
[on GitHub](https://github.com/QuaLiKiz-group/QuaLiKiz).
This repository contains the source for the Python package qualikiz_tools.
Use the qualikiz_tools CLI (Command Line Interface) to generate, run and
analyze QuaLiKiz runs. For more advanced usage scenarios the modules
themselves can be used in other python scripts. For example, the
[QuaLiKiz Neural Network](https://github.com/QuaLiKiz-group/QuaLiKiz-NeuralNetwork)
training set was generated in this way.


## Install
The recommended way to install qualikiz_tools is to use pip. Although
installation is not strictly necessary to use the python modules,
it is advised to install anyway for the full power of the CLI.

1. [Clone the repository from GitHub](https://help.github.com/articles/cloning-a-repository/).
    * If you want to install as submodule of QuaLiKiz (preferred)

            git clone git@github.com:QuaLiKiz-group/QuaLiKiz.git

      and then

          git submodule init
          git submodule update

    * If you want to install standalone, clone using (not recommended)

            git clone git@github.com:QuaLiKiz-group/QuaLiKiz-pythontools.git

2. (Recommended) Install [xarray dependencies](http://xarray.pydata.org/en/stable/installing.html)

        apt-get install netcdf-dev hdf5
        pip install netcdf4

3. Install qualikiz_tools. This fully installs it in developer mode

        pip install -e .[test]

## Usage
Examples scripts can be found in qualikiz_tools/examples. A workflow example is
given below:

1. Generate a template QuaLiKiz run directory using the CLI

        qualikiz_tools create example
        cd runs/example

2. Adjust the `parameters.json` to your liking (optional)
3. Generate the input binaries using the CLI

        qualikiz_tools input generate .

4. Submit the job. We assume the [machine specific](qualikiz_tools/machine_specific) files exist. Use 'bash' if they do not, which assumes you can run an mpi program using `mpirun`

        qualikiz_tools launcher launch bash .

5. After the job is done, convert the output to netCDF.

        qualikiz_tools output to_netcdf .

6. Plot your netCDF file, for example:

        qualikiz_tools plot --flux ef .

## FAQ
* How do I run the unit tests?

        python setup.py test

* How do I find out what each CLI command does?

        qualikiz_tools help
        qualikiz_tools <command> help
