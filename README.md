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

1. Clone the repository from GitHub.
    * If you want to install as submodule of QuaLiKiz (preferred)

            git clone git@github.com:QuaLiKiz-group/QuaLiKiz.git

      or

            git clone https://github.com/QuaLiKiz-group/QuaLiKiz.git

      and then

            git submodule init
            git submodule update

    * If you want to install standalone, just clone using (preferred)

            git clone git@github.com:QuaLiKiz-group/QuaLiKiz-pythontools.git

      or

            git clone https://github.com/QuaLiKiz-group/QuaLiKiz-pythontools.git

2. (Recommended) Install [xarray dependencies](http://xarray.pydata.org/en/stable/installing.html)

        apt-get install netcdf-dev hdf5
        pip install netcdf4

3. Install qualikiz_tools. This fully installs it in developer mode

        pip install -e .[test]

## Usage
Examples scripts can be found in qualikiz_tools/examples. A workflow example is
given below:

1. Generate a template QuaLiKiz run directory using examples/mini.py

        qualikiz_tools create mini
        cd runs/mini

2. Adjust the `parameters.json` to your liking
3. Generate the input using the run.py script

        ./run.py input

4. Submit the job
    * Manually (for example, on Edison)

            sbatch edison.sbatch

    * Automatically

            ./run.py go

    Step 3 and 4 can be done together by running

        ./run.py inputgo

5. After the job is done, convert the output to netCDF (as the mini-example is no hyper-rectangle,
    the `--nocube` flag makes sure that the resulted dataset is not folded.

        qualikiz_tools output --nocube to_netcdf .

6. Look at your netCDF file, for example, from within `IPython`

        import xarray as xr
        ds = xr.open_dataset('mini.nc')
        print(ds)

## FAQ
* How do I run the unit tests?

        python setup.py test
