"""
Copyright Dutch Institute for Fundamental Energy Research (2016-2017)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import os
import copy
from warnings import warn
from collections import OrderedDict
from itertools import chain
import sys
import array
import gc

import pandas as pd
import numpy as np
import xarray as xr

output_meth_0_sep_0 = {
    'gam'               : None,
    'ome'               : None,
    'pfe'               : None,
    'pfi'               : None,
    'efe'               : None,
    'efi'               : None,
    'vfi'               : None,
    'vri'               : None,
    'pfe_cm'            : None,
    'pfi_cm'            : None,
    'efe_cm'            : None,
    'efi_cm'            : None,
    'vfi_cm'            : None,
    'ecoefs'            : None, #No suffix
    'npol'              : None, #No suffix
    'cftrans'           : None  #No suffix
    }

output_meth_0_sep_1 = {
    'efeETG'            : None,
    'efeITG'            : None,
    'efeTEM'            : None,
    'efiITG'            : None,
    'efiTEM'            : None,
    'pfeITG'            : None,
    'pfeTEM'            : None,
    'pfiITG'            : None,
    'pfiTEM'            : None,
    'vfiITG'            : None,
    'vfiTEM'            : None,
}

output_meth_1_sep_0 = {
    'cke'               : None, #No suffix
    'cki'               : None, #No suffix
    'dfe'               : None,
    'dfi'               : None,
    'vte'               : None,
    'vti'               : None,
    'vce'               : None,
    'vci'               : None
}

output_meth_1_sep_1 = {
    'dfeITG'            : None,
    'dfeTEM'            : None,
    'dfiITG'            : None,
    'dfiTEM'            : None,
    'vriITG'            : None,
    'vriTEM'            : None,
    'vteITG'            : None,
    'vteTEM'            : None,
    'vtiITG'            : None,
    'vtiTEM'            : None,
    'vceITG'            : None,
    'vceTEM'            : None,
    'vciITG'            : None,
    'vciTEM'            : None
}

output_meth_2_sep_0 = {
    'ceke'              : None,
    'ceki'              : None,
    'chiee'             : None,
    'chiei'             : None,
    'vece'              : None,
    'veci'              : None,
    'vene'              : None,
    'veni'              : None,
    'veri'              : None
}

output_meth_2_sep_1 = {
    'chieeETG'          : None,
    'chieeITG'          : None,
    'chieeTEM'          : None,
    'chieiITG'          : None,
    'chieiTEM'          : None,
    'veceETG'           : None,
    'veceITG'           : None,
    'veceTEM'           : None,
    'veciITG'           : None,
    'veciTEM'           : None,
    'veneETG'           : None,
    'veneITG'           : None,
    'veneTEM'           : None,
    'veniITG'           : None,
    'veniTEM'           : None,
    'veriITG'           : None,
    'veriTEM'           : None
}

primi_meth_0 = {
    'Lcirce'            : None,
    'Lcirci'            : None,
    'Lecirce'           : None,
    'Lecirci'           : None,
    'Lepiege'           : None,
    'Lpiege'            : None,
    'Lpiegi'            : None,
    'Lvcirci'           : None,
    'Lvpiegi'           : None,
    'fdsol'             : None,
    'jonsolflu'         : None,
    'modeshift'         : None,
    'modewidth'         : None,
    'sol'               : None,
    'solflu'            : None,
    'ntor'              : None,
    'distan'            : None,
    'kperp2'            : None,
    'kymaxETG'          : None,
    'kymaxITG'          : None
    }

primi_meth_1 = {
    'Lcircgne'          : None,
    'Lcircgni'          : None,
    'Lcircgte'          : None,
    'Lcircgti'          : None,
    'Lcircgui'          : None,
    'Lcircce'           : None,
    'Lcircci'           : None,
    'Lpiegce'           : None,
    'Lpiegci'           : None,
    'Lpieggte'          : None,
    'Lpieggti'          : None,
    'Lpieggui'          : None,
    'Lpieggne'          : None,
    'Lpieggni'          : None
}

primi_meth_2 = {
    'Lecircce'          : None,
    'Lecircci'          : None,
    'Lecircgne'         : None,
    'Lecircgni'         : None,
    'Lecircgte'         : None,
    'Lecircgti'         : None,
    'Lecircgui'         : None,
    'Lepiegce'          : None,
    'Lepiegci'          : None,
    'Lepieggne'         : None,
    'Lepieggni'         : None,
    'Lepieggui'         : None,
    'Lepiegi'           : None,
    'Lepieggte'         : None,
    'Lepieggti'         : None
}

debug_eleclike = {
    'Ane'               : None,
    'Ate'               : None,
    'Aupar'             : None,
    'Autor'             : None,
    'Machpar'           : None,
    'Machtor'           : None,
    'x'                 : None,
    'Zeff'              : None,
    'Bo'                : None,
    'gammaE'            : None,
    'ne'                : None,
    'Nustar'            : None,
    'q'                 : None,
    'Ro'                : None,
    'Rmin'              : None,
    'smag'              : None,
    'Te'                : None,
    'alpha'             : None,
    'modeflag'          : None,
    'rho'               : None
}


debug_ionlike = {
    'Ai'                : None,
    'Ani'               : None,
    'Ati'               : None,
    'Zi'                : None,
    'typei'             : None,
    'normni'            : None,
    'Ti'                : None
}

debug_single = {
    'dimn'              : None,
    'dimx'              : None,
    'nions'             : None,
    'numsols'           : None,
    'coll_flag'         : None,
    'maxpts'            : None,
    'maxruns'           : None,
    'R0'                : None,
    'typee'             : None,
    'relacc1'           : None,
    'relacc2'           : None,
    'collmult'          : None,
    'ETGmult'           : None,
    'rot_flag'          : None,
    'separateflux'      : None,
    'timeout'           : None,
    'phys_meth'         : None,
    'verbose'           : None
}

debug_special = {'kthetarhos': None,
                 'phi': None}
# Some magic to group all datasets. In principe the granularity
# per subset is not needed, but we keep it for legacy purposes
output_subsets = OrderedDict()
output_subsets.update(output_meth_0_sep_0)
output_subsets.update(output_meth_0_sep_1)
output_subsets.update(output_meth_1_sep_0)
output_subsets.update(output_meth_1_sep_1)
output_subsets.update(output_meth_2_sep_0)
output_subsets.update(output_meth_2_sep_1)
primi_subsets = OrderedDict()
primi_subsets.update(primi_meth_0)
primi_subsets.update(primi_meth_1)
primi_subsets.update(primi_meth_2)
debug_subsets = OrderedDict()
debug_subsets.update(debug_eleclike)
debug_subsets.update(debug_ionlike)
debug_subsets.update(debug_single)
debug_subsets.update(debug_special)

subsets = OrderedDict()
subsets.update(output_subsets)
subsets.update(primi_subsets)
subsets.update(debug_subsets)

suffix = '.dat'
numecoefs = 13
numicoefs = 7
ntheta = 64

def determine_sizes(rundir, folder='debug', keepfile=True):
    """ Determine the sizes needed for re-shaping arrays

    Load output from debug folder. The values of dimx, dimn, nions and numsols
    are needed to reshape all the other output arrays, so this should be done
    first.

    Args:
        rundir:   The root directory of the run. Should contain the debug folder

    Kwargs:
        folder:   Name of the debug folder
        keepfile: Delete the file after reading. NOT RECOMMENDED

    Returns:
        sizes:    A dictionary with the four sizes.
    """
    names = ['dimx', 'dimn', 'nions', 'numsols']
    sizes = OrderedDict()
    for name in names:
        path_ = os.path.join(rundir, folder, name + suffix)
        with open(path_, 'rb') as file:
            data = np.loadtxt(file)
            sizes[name] = int(data)
        if not keepfile:
            os.remove(path_)
    if sizes:
        return sizes
    else:
        raise Exception('Could not read sizes from ' + os.path.join(rundir, folder, name + suffix))

def determine_dims_debug(name):
    if name in debug_eleclike:
        dims = ['dimx']
    elif name in debug_ionlike:
        dims = ['dimx', 'nions']
    elif name in debug_single:
        dims = None
    elif name in ['kthetarhos']:
        dims = ['dimn']
    elif name in ['phi']:
        dims = ['ntheta', 'dimx']
    else:
        raise Exception("Could not find dims for " + name + "'")
    return dims

def load_file(rundir, folder, filename, verbose=False, genfromtxt=False):
    dir = os.path.join(rundir, folder)
    basename = filename + suffix
    path_ = os.path.join(dir, basename)
    with open(path_, 'rb') as file:
        if verbose:
            print('loading ' + basename.ljust(20) + ' from ' + dir)
        try:
            if genfromtxt:
                data = np.genfromtxt(file)
            else:
                data = np.loadtxt(file)
        except Exception as ee:
            print('Exception loading ' + file.name)
            raise
    return data

def add_missing_dims(sizes, data, dims):
    dimx, dimn, nions, numsols = sizes.values()
    if dims is not None:
        for dim, dim_size in sizes.items():
            if dim_size == 1 and dim in dims:
                di = dims.index(dim)
                if len(data.shape) != len(dims):
                    data = np.expand_dims(data, axis=di)
    return data

def convert_debug(sizes, rundir, folder='debug', verbose=False,
                  genfromtxt=False, keepfile=True):
    """ Convert the debug folder to netcdf

    Load the output from the debug folder and convert it to netcdf. Note that
    this function does not write anything to disk! The resulting dataset is
    meant to be passed to convert_output and convert_primitive so that the
    final result can be written to file.

    Args:
        sizes:      A dictionary with the sizes for reshaping the arrays. Usually
                    generated with determine_sizes
        rundir:     The root directory of the run. Should contain the debug folder

    Kwargs:
        folder:     Name of the debug folder
        verbose:    Output a message per file converted
        genfromtxt: Use genfromtxt instead of loadtxt. Slower and loads
                    unreadable values as nan
        keepfile:   Keep the file after reading. HIGHLY RECOMMENDED

    Returns:
        ds:         The netcdf dataset
    """
    ds = xr.Dataset()
    dimx, dimn, nions, numsols = sizes.values()
    for name in debug_subsets:
        try:
            data = load_file(rundir, folder, name, verbose=verbose, genfromtxt=genfromtxt)
        except FileNotFoundError:
            print('not found' + os.path.join(rundir, folder, name + suffix))
            continue
        # Skip loading these, as they will be saved implicitly
        if name in ['dimx', 'dimn', 'nions', 'numsols']:
            continue
        dims = determine_dims_debug(name)
        # Add 'missing' dimensions squeezed out by loading from disk
        data = add_missing_dims(sizes, data, dims)

        if name == 'modeflag':
            ds[name] = xr.DataArray(data, dims=dims)
        else:
            ds.coords[name] = xr.DataArray(data, dims=dims)
        if not keepfile:
            os.remove(path_)

    # Nothing in debug depends on numsols, but add it for later use
    ds.coords['numsols'] = xr.DataArray(list(range(0, numsols)), dims='numsols')
    return ds


def convert_output(ds, sizes, rundir, folder='output', verbose=False,
                   genfromtxt=False, keepfile=True):
    """ Convert the output folder to netcdf

    Load the output from the output folder and convert it to netcdf. Note that
    this function does not write anything to disk! The resulting dataset is
    meant to be passed to convert_primitive so that the final result
    can be written to file.

    Args:
        ds:         Dataset the loaded data should be appended to
        sizes:      A dictionary with the sizes for reshaping the arrays. Usually
                    generated with determine_sizes
        rundir:     The root directory of the run. Should contain the output folder

    Kwargs:
        folder:     Name of the output folder
        verbose:    Output a message per file converted
        genfromtxt: Use genfromtxt instead of loadtxt. Slower and loads
                    unreadable values as NaN
        keepfile:   Keep the file after reading. HIGHLY RECOMMENDED

    Returns:
        ds:         The netcdf dataset
    """
    dimx, dimn, nions, numsols = sizes.values()
    for name in output_subsets:
        if (name not in ['cke', 'ceke', 'cki', 'ceki', 'ion_type', 'ecoefs', 'npol', 'cftrans']
                and not name.endswith('_cm')):
            names = [name + '_SI', name + '_GB']
        else:
            names = [name]
        for name in names:
            try:
                data = load_file(rundir, folder, name, verbose=verbose, genfromtxt=genfromtxt)
            except FileNotFoundError:
                print('not found' + os.path.join(rundir, folder, name + suffix))
                continue
            if name == 'ecoefs':
                dims = ['dimx', 'ionelec', 'ecoefs']
                tmp = xr.DataArray(data.reshape(dimx, nions+1, numecoefs),
                                   dims=dims, name=name)
                ds[name + 'e'] = tmp.sel(ionelec=0)
                ds[name + 'i'] = tmp.sel(ionelec=slice(1, None)).rename({'ionelec': 'nions'})
            else:
                if name.startswith('gam') or name.startswith('ome'):
                    #dims_orig = ['numsols', 'dimx', 'dimn']
                    data = data.reshape(numsols, dimx, dimn)
                    data =  data.transpose(1, 2, 0)
                    dims = ['dimx', 'dimn', 'numsols']
                elif name in ['cke', 'ceke']:
                    dims = ['dimx']
                elif  name in ['cki', 'ceki', 'ion_type']:
                    dims = ['dimx', 'nions']
                elif name.endswith('i_cm'):
                    #dims_orig = ['nions', 'dimx', 'dimn']
                    data = data.reshape(nions, dimx, dimn)
                    data = data.transpose(1, 2, 0)
                    dims = ['dimx', 'dimn', 'nions']
                elif name.endswith('e_cm'):
                    #dims_orig = ['dimx', 'dimn']
                    data = data.reshape(dimx, dimn)
                    dims = ['dimx', 'dimn']
                elif name == 'npol':
                    dims = ['dimx', 'ntheta', 'nions']
                    data = data.reshape(dimx, ntheta, nions)
                elif name == 'cftrans':
                    dims = ['dimx', 'nions', 'numicoefs']
                    data = data.reshape(dimx, nions, numicoefs)
                else:
                    basename = name[:-3]
                    if any([basename.endswith(mode) for mode in ['ETG', 'ITG', 'TEM']]):
                        basename = basename[:-3]
                    if basename.endswith('e'):
                        dims = ['dimx']
                    elif basename.endswith('i'):
                        dims = ['dimx', 'nions']
                    else:
                        raise Exception('Could not process \'' + name + '\'')

                data = add_missing_dims(sizes, data, dims)
                ds[name] = xr.DataArray(data, dims=dims, name=name)
            if not keepfile:
                os.remove(path_)
    return ds


def convert_primitive(ds, sizes, rundir, folder='output/primitive', verbose=False,
                      genfromtxt=False, keepfile=True):
    """ Convert the output/primitive folder to netcdf

    Load the output from the output/primitive folder and convert it to netcdf.
    Note that this function does not write anything to disk! The resulting
    dataset should be written to file using xarray's to_netcdf function.

    Args:
        ds:         Dataset the loaded data should be appended to
        sizes:      A dictionary with the sizes for reshaping the arrays. Usually
                    generated with determine_sizes
        rundir:     The root directory of the run. Should contain the output folder

    Kwargs:
        folder:     Name of the output/primitive folder
        verbose:    Output a message per file converted
        genfromtxt: Use genfromtxt instead of loadtxt. Slower and loads
                    unreadable values as NaN
        keepfile:   Keep the file after reading. HIGHLY RECOMMENDED

    Returns:
        ds:         The netcdf dataset
    """
    dimx, dimn, nions, numsols = sizes.values()
    for name in primi_subsets:
        if name in ['fdsol', 'jonsolflu', 'modeshift', 'modewidth', 'sol', 'solflu']:
            names = ['r' + name, 'i' + name]
        else:
            names = [name]
        for name in names:
            try:
                data = load_file(rundir, folder, name, verbose=verbose, genfromtxt=genfromtxt)
            except FileNotFoundError:
                print('not found' + os.path.join(rundir, folder, name + suffix))
                continue
            if name.endswith('i'):
                #dims_orig = ['numsols', 'nions', 'dimx', 'dimn']
                data = data.reshape(numsols,nions,dimx,dimn)
                data = data.transpose(2, 3, 1, 0)
                dims = ['dimx', 'dimn', 'nions', 'numsols']
            elif name.endswith('e') or name in ['rfdsol', 'ifdsol', 'isol', 'rsol']:
                #dims_orig = ['numsols', 'dimx', 'dimn']
                data = data.reshape(numsols, dimx, dimn)
                data = data.transpose(1, 2, 0)
                dims = ['dimx', 'dimn', 'numsols']
            elif name in ['kymaxETG', 'kymaxITG']:
                dims = ['dimx']
            else:
                dims = ['dimx', 'dimn']
            data = add_missing_dims(sizes, data, dims)
            ds[name] = xr.DataArray(data, dims=dims, name=name)
            if not keepfile:
                os.remove(path_)
    return ds


def squeeze_coords(ds, dim):
    """ Squeezes Coordinates with duplicate values

    Normally, a dataset loaded from a QuaLiKizRun contains a lot of
    duplicate values. For easy-of-use, squeeze these arrays to a single
    value. For arrays that contain data of ions, squeeze it to an array
    of length nions.

    Args:
        ds:  Dataset with coordinates to squeeze
        dim: Dimension to squeeze over

    Returns:
        ds: The netcdf dataset with coordinates squeezed
    """
    for name, item in ds.coords.items():
        if dim in item.dims:
            new = np.unique(item)
            if len(new) == 1 and len(item) != 1:
                ds.coords[name] = xr.DataArray(float(new))
            elif 'nions' in item.dims and name != 'nions':
                squeezable = True
                # Check if we can squeeze ions
                for i in range(item['nions'].size):
                    squeezable &= (len(np.unique(item.sel(nions=i).values)) == 1)
                if squeezable:
                    ds.coords[name] = xr.DataArray(item[0,:].values,
                                                   coords={'nions': item['nions']},
                                                   dims=['nions'])
                # Check if we can squeeze dimx
                squeezable = True
                for i in range(item['dimx'].size):
                    squeezable &= (len(np.unique(item.sel(dimx=i).values)) == 1)
                if squeezable:
                    ds.coords[name] = xr.DataArray(item[:,0].values,
                                                   coords={'dimx': item['dimx']},
                                                   dims=['dimx'])
    return ds


def remove_dependent_axes(ds, Te_var='Te'):
    """ Remove Coordinates that depend on eachother

    Normally, a dataset loaded from a QuaLiKizRun contains some coordinates
    that are not orthogonal, or, that do depend on eachother. For example,
    Ti_Te depends both on Ti and on Te. As we assume orthogonality for most
    functions, move these coordinates to the DataVariables.

    Args:
        ds: Dataset with dependent Coordinates to remove

    Kwargs:
        Te_var: Which variable to use as Te measure: Nustar or Te [Default: 'Te']

    Returns:
        xarray.DataSet with dependent Coordinates removed
    """
    Te_vars = ['Te', 'Nustar']
    if Te_var not in Te_vars:
        raise ValueError('Te_var {!s} should be one of {!s}'.format(Te_var, Te_vars))
    # Ni is captured in Zeff
    if 'normni' in ds.coords:
        ds = ds.reset_coords('normni')

    # Tix is captured in Ti_Te
    if 'Te' in ds.coords and 'Ti' in ds.coords:
        Ti_Te_rel = np.around(ds.coords['Ti'] / ds.coords['Te'], 5)
        ds.coords['Ti_Te'] = Ti_Te_rel
        ds = ds.reset_coords('Ti')

    # Tex is already captured in Nustar
    if 'Te' in ds.coords and 'Nustar' in ds.coords:
        if Te_var == 'Nustar':
            ds = ds.reset_coords('Te')
        elif Te_var == 'Te':
            ds = ds.reset_coords('Nustar')

    # rho and x are the same thing
    if 'rho' in ds.coords and 'x' in ds.coords:
        ds = ds.reset_coords('rho')

    # Remove placeholder for kthetarhos
    if 'dimn' in ds.dims and 'kthetarhos' in ds.coords:
        ds = ds.swap_dims({'dimn': 'kthetarhos'})
        try:
            ds = ds.drop('dimn')
        except ValueError:
            warn('WARNING! dimn not found in dataset. Might be nothing, debugging still on TODO list')
    return ds


def squeeze_dataset(ds, Te_var='Te', extra_squeeze=None):
    """ Remove Coordinates that depend on eachother and squeeze duplicates

    Normally, a dataset loaded from a QuaLiKizRun contains some coordinates
    that are not orthogonal, or, that do depend on eachother. For example,
    Ti_Te depends both on Ti and on Te. As we assume orthogonality for most
    functions, move these coordinates to the DataVariables.
    Also, a dataset loaded from a QuaLiKizRun contains a lot of
    duplicate values. For easy-of-use, squeeze these arrays to a single
    value. For arrays that contain data of ions, squeeze it to an array
    of length nions.

    Args:
        ds: Dataset with dependent Coordinates to remove

    Kwargs:
        Te_var: See `remove_dependent_axes`
        extra_squeeze: List of coordinates to move to data_vars

    Returns:
        xarray.DataSet with data_vars squeezed
    """
    ds.load()

    # Move some axes we know depend on eachother to data.
    ds = remove_dependent_axes(ds, Te_var=Te_var)

    ds = squeeze_coords(ds, 'dimx')

    # Squeeze Ane and Ani into An
    if 'Ane' in ds.coords and 'Ani' in ds.coords:
        if ds['Ane'].equals(ds['Ani']):
            ds.coords['An'] = ds['Ane'].copy()
            ds = ds.drop('Ane')
            ds = ds.drop('Ani')

    # Squeeze Ate and Ati into At
    if 'Ate' in ds.coords and 'Ati' in ds.coords:
        if ds['Ate'].equals(ds['Ati']):
            ds.coords['At'] = ds['Ate'].copy()
            ds = ds.drop('Ate')
            ds = ds.drop('Ati')

    # Squeeze constant for dimx
    ds = squeeze_coords(ds, 'dimx')

    # Move metadata to attrs
    ds = to_meta_0d(ds)
    if extra_squeeze is not None:
        for coord in extra_squeeze:
            if coord in ds.coords:
                ds.reset_coords(names=coord, inplace=True)
            else:
                warn('{!s} not in dataset, cannot be squeezed'.format(coord))
                from IPython import embed
                embed()
    return ds

def to_meta_0d(ds):
    """ Move 0d variables to attrs """
    for name, item in ds.items():
        if item.shape == ():
            ds.attrs[name] = float(item)
            ds = ds.drop(name)
    return ds

#TODO: Implement unsqueezing function for converting back to a QuaLiKizRun
def unsqueeze_dataset(ds):
    raise NotImplementedError
    # Readd placeholder for kthetarhos
    name = 'kthetarhos'
    if name in ds.coords:
        ds.coords['dimn'] = xr.DataArray(range(len(ds[name])), coords={name: ds[name]}, name=ds[name].name, attrs=ds[name].attrs, encoding=ds[name].encoding)
        ds = ds.swap_dims({name: 'dimn'})
        ds = ds.drop(name)
    return ds

    # Move metadata to coords
    for name, item in ds.attrs.items():
        ds.coords[name] = item

    # Unsqueeze constants for dimx
    print(ds.dims)
    for name, item in ds.coords.items():
        if 'dimx' not in item.dims and name not in ds.dims:
            print(name)
            #ds.drop(name)
            if 'nions' not in item.dims:
                ds.coords[name] = xr.DataArray(np.repeat(item.data, ds['dimx'].size), coords={'dimx': ds['dimx'].data}, name=ds[name].name, attrs=ds[name].attrs, encoding=ds[name].encoding)
            else:
                ds.coords[name] = xr.DataArray(np.repeat(np.atleast_2d(item.data), ds['dimx'].size, axis=0), coords=OrderedDict([('dimx', ds['dimx'].data), ('nions', ds['nions'].data)]), name=ds[name].name, attrs=ds[name].attrs, encoding=ds[name].encoding)
    return ds

    # Unsqueeze At back to Ate and Ati
    try:
        ds.coords['Ate'] = ds['At'].copy(deep=True)
        ds.coords['Ati'] = ds['At'].copy(deep=True)
        ds = ds.drop('At')
    except KeyError:
        pass

    # Unsqueeze An back to Ane and Ani
    try:
        ds.coords['Ane'] = ds['An'].copy(deep=True)
        ds.coords['Ani'] = ds['An'].copy(deep=True)
        ds = ds.drop('An')
    except KeyError:
        pass

    # Unsqueeze equal ions
    for name, item in ds.coords.items():
        if 'nions' not in item.dims and name not in ds.dims and name in debug_ionlike:
            ds.coords[name] = xr.DataArray(np.repeat(np.atleast_2d(item.data), ds['nions'].size, axis=0).T, coords=OrderedDict([('dimx', ds['dimx'].data), ('nions', ds['nions'].data)]), name=ds[name].name,attrs=ds[name].attrs, encoding=ds[name].encoding)

    # Move metadata back to coords
    dropped = []
    for name, item in ds.attrs.items():
        if name in debug_single:
            dropped.append(name)
            ds.coords[name] = item
        for name in dropped:
            del ds.attrs[name]

    return ds

def orthogonalize_dataset(ds, verbose=False):
    """ Convert dataset depending on dimx to orthogonal dimensions

    As a QuaLiKizRun is generally a scan over a few parameters, recast all
    arrays to an orthogonal base. This will lead to many missing values if
    the scan parameters do not form a (hyper)-rectangle together.

    Args:
        ds: The dataset to be orhogonalized

    Kwargs:
        verbose: Print a message for every DataVar to be orhogonalized

    Returns:
        newds: Orthogonalized dataset, not dependant on the original
    """
    #TODO: Find solution that is quick enough without loading everything
    ds.load()

    # Determine the new (orthogonal) dimensions
    ortho_dims = [coord for name, coord in ds.coords.items() if name not in ds.dims and ('dimx', ) == coord.dims]
    new_dims = OrderedDict([(dim.name, np.unique(dim.values)) for dim in ortho_dims])

    # Temporarely convert coordinates with dimx and one or more other dims to datavars so they get folded
    duo_coords = [(name, coord) for name, coord in ds.coords.items() if name not in ds.dims and ('dimx', ) != coord.dims and 'dimx' in coord.dims]
    duo_coords = OrderedDict(duo_coords)
    ds.reset_coords(names=duo_coords.keys(), inplace=True)

    # Create new dataset with these dimensions, plus all old non-dimx dims
    dims = copy.deepcopy(new_dims)
    for name in ds.dims:
        if name != 'dimx':
            dims[name] = ds[name]
    newds = xr.Dataset(coords=dims)

    # First determine the indexes in the new arrays dependant on dimx
    ilist = []
    tmpi = np.empty(len(new_dims), dtype='int64')
    for x in ds['dimx']:
        for i, new_dim in enumerate(new_dims):
            tmpi[i] = int(np.where(new_dims[new_dim] == float(x[new_dim].data))[0])
        ilist.append(tuple(tmpi))

    # Then recast all data_vars to the new shapes
    for name in list(ds.data_vars.keys()):
        if verbose:
            print(name)
        item = ds[name]
        shape = [len(i) for i in new_dims.values()]
        shape += [len(item[x]) for x in item.dims if x != 'dimx']
        placeholder = np.full(shape, np.nan)
        if name == 'phi':
            data = ds[name].data.T
        else:
            data = ds[name].data
        for i, datax in enumerate(data):
            placeholder[ilist[i]] = datax
            newcoords = copy.deepcopy(new_dims)
            for dim in item.dims:
                if dim != 'dimx':
                    newcoords[dim] = ds[dim]

        # To save memory, we delete the old ds entry
        del ds[name]
        newds[name] = xr.DataArray(placeholder, coords=newcoords, dims=newcoords.keys())

    # Copy temporarly converted coordinates back to coordinates
    newds.set_coords(duo_coords.keys(), inplace=True)

    # Copy over attributes
    for attr in ds.attrs:
        newds.attrs[attr] = ds.attrs[attr]

    return newds

def add_dims(ds, newdims):
    """ Add a new dimension to a dataset

    Add a dimension to all DataVariables in the dataset. Because of the way
    netcdf is structured, this means that the whole dataset has to be copied
    over

    Args:
        ds:      Dataset to which the dimensions should be added
        newdims: List of names of the dimensions to be added

    Returns:
        newds: Dataset, not dependant on the original, with dimensions added
    """
    newds = xr.Dataset()
    # Put all non-dim coordinates in new ds
    for name, item in ds.coords.items():
        if name not in ds.dims and name not in newdims:
            newds.coords[name] = item

    # Add all dimensions to new ds
    for name in chain(ds.dims.keys(), newdims):
        values = ds[name].values
        if values.shape == ():
            newds[name] = [values]
        else:
            newds[name] = values

    # All new data variables should depend on the new dimensions
    for name, item in ds.data_vars.items():
        newcoords = OrderedDict()
        newitemdims = item.dims + tuple(newdims)
        olddims = item.dims
        for dim in newdims:
            if dim in olddims:
                raise Exception('Cannot add dimension {!s}. Already a dimension of {!s}'.format(dim, name))

        for dimname in olddims:
            newcoords[dimname] = ds[dimname]

        for dimname in newdims:
            item = np.expand_dims(item, -1)
            newcoords[dimname] = newds[dimname]

        try:
            newds[name] = xr.DataArray(item, dims=newitemdims, coords=newcoords,
                                       name=ds[name].name, attrs=ds[name].attrs,
                                       encoding=ds[name].encoding)
        except:
            print('Something wrong with creating new-dimmed DataArray. Debugging..')
            from IPython import embed
            embed()

    # Copy the attributes
    for name, item in ds.attrs.items():
        newds.attrs[name] = item


    return newds

def merge_many_lazy_snakes(path, dss, datavars=None, verbose=False, netcdf_kwargs=None, **kwargs):
    if os.path.exists(path):
        raise OSError('{!s} exists! Refusing to overwrite')

    if netcdf_kwargs is None:
        netcdf_kwargs = {}

    if datavars is None:
        datavars = list(dss[0].data_vars.keys())

    xr.Dataset().to_netcdf(path, 'w', **netcdf_kwargs)

    for name in datavars:
        if verbose:
            print('Merging {!s}'.format(name))
        vars = [ds[name] for ds in dss]
        ds = xr.concat(vars, dim='snakedim')
        ds.to_netcdf(path, 'a', **netcdf_kwargs)
        del vars
        gc.collect()
    return xr.open_dataset(path)

def merge_many_orthogonal(dss, datavars=None, verbose=False, **kwargs):
    newds = dss[0]
    newds.load()
    for ds in dss[1:]:
        ds.load()
        newds = merge_orthogonal(newds, ds)
        ds.close()

    newds = sort_dims(newds)

    return newds

def find_nonmatching_coords(ds1, ds2):
    """ Find non-equal coordinates in datasets """
    nonmatching = []
    for name in ds1.coords:
        if np.all(ds1[name] != ds2[name]):
            nonmatching.append(name)

    return nonmatching

def merge_orthogonal(ds1, ds2, datavars=None, verbose=False):
    """ Left join two orthogonal datasets.

    Merge two datasets together. These datasets should only contain
    orthogonal dimensions, so first orthogonalize with orthogonalize_dataset.
    Falls back to Xarrays merge when only one dimension is different,
    and tries to merge smartly when more dimensions are different. Note that
    the second method is slow and uses a lot of RAM

    Args:
        ds1: First datasets to merge
        ds2: Datasets to merge ds1 with

    Kwargs:
        datavars: DataVariables to keep in the merged dataset
        verbose:  Print message for each variables to be merged
    """
    nonmatching = find_nonmatching_coords(ds1, ds2)
    if len(nonmatching) == 0:
        raise NotImplementedError
    elif len(nonmatching) == 1:
        if datavars:
            raise NotImplementedError
        newds = xr.concat([ds1, ds2], dim=nonmatching[0])
    else:
        if not datavars:
            datavars = list(ds1.data_vars.keys())
        for nonmatch in nonmatching:
            if nonmatch not in ds1.dims:
                if verbose:
                    print('adding dim ' + nonmatch)
                ds1 = add_dims(ds1, nonmatching)
            if nonmatch not in ds2.dims:
                if verbose:
                    print('adding dim ' + nonmatch)
                ds2 = add_dims(ds2, nonmatching)
        newds = xr.Dataset()
        for name in ds1.data_vars:
            if name in datavars:
                if verbose:
                    print('merging ' + name)
                # Concatenate objects. We need to supply an existing dimension to
                # Prevent the creation of a new dimension
                newds[name] = xr.concat((ds1[name], ds2[name]), nonmatching[0],
                                        coords='all', compat='identical')
                del ds1[name]
                del ds2[name]
        for nonmatch in nonmatching:
            newds = squeeze_coords(newds, nonmatch)
        newds.attrs = ds1.attrs

    return newds

def sort_dims(ds):
    """ Sort dimensions and DataVars using numpy.sort """
    for dim in ds.dims:
        ds = ds.reindex(**{dim: np.sort(ds[dim])})
    return ds

def to_input_json(ds, inputdir='input'):
    """ Create an input json file from dataset
    This functions created a input JSON file using the coordinates
    as scan values. The cleanest JSON will be generated if a
    squeezed dataset is used.
    """
    ignore = ['Zeff', 'Nustar']
    conversion_dict = {'Tex': 'Te',
                       'Nex': 'ne',
                       'ion_type': 'typei',
                       'ninorm': 'normni',
                       'Tix': 'Ti'}
    for name, item in ds.coords.items():
        print(name)
        dimx = len(ds['dimx'])
        nions = len(ds['nions'])
        if name in ['dimx', 'dimn', 'nions', 'numsols']:
            bytevalues = [len(item)]
        else:
            if 'nions' in item.dims:
                bytevalues = item.stack(dim=('nions', 'dimx')).data
            elif 'dimx' in item.dims or name == 'kthetarhos':
                bytevalues = item.data
            else:
                bytevalues = [item.data]
        print(bytevalues)
        value = array.array('d', bytevalues)
        if name  in conversion_dict:
            name = conversion_dict[name]

        if name not in ignore:
            with open(os.path.join(inputdir, name + '.bin'), 'wb') as file_:
                value.tofile(file_)
    fake = {'alphax': 0.,
            'danisdre': 0.,
            'anise': 1.}

    for name, value in fake.items():
        with open(os.path.join(inputdir, name + '.bin'), 'wb') as file_:
            array.array('d', np.full(dimx, value)).tofile(file_)

    fake = {'danisdri': 0.,
            'anisi': 1.}

    for name, value in fake.items():
        with open(os.path.join(inputdir, name + '.bin'), 'wb') as file_:
            array.array('d', np.full(nions*dimx, value)).tofile(file_)
    fake = {'phys_meth': 1.,
            'typee': 1.,
            'verbose': 1.}

    for name, value in fake.items():
        with open(os.path.join(inputdir, name + '.bin'), 'wb') as file_:
            array.array('d', [value]).tofile(file_)

    with open(os.path.join(inputdir, 'rho' + '.bin'), 'wb') as file_:
        array.array('d', ds['x'].data).tofile(file_)

def xarray_to_pandas(ds):
    """ Convert xarray.DataSet to dict of pd.DataFrame

    Panda DataFrames are usually easier to understand, as they are
    equivalent to a 2D table. With this function all variables in
    the dataset will be converted to a DataFrame grouped together
    on the shape of the dimensions.

    Returns:
        A dictionary with pandas.DataFrame
    """
    ds = to_meta_0d(ds)
    ds = ds.reset_coords()
    panda_dict = {}

    #coords = ds.drop([coord for coord in ds.coords.keys() if coord not in ds.dims])

    for name, var in ds.items():
        #if name in ds.coords:
        #    continue
        tablename = var.dims
        df = var.to_dataframe()
        # Drop coords
        df = df.drop([col for col in df.columns if col in ds.coords], axis=1)
        if df.size > 0:
            try:
                panda_dict[tablename] = panda_dict[tablename].join(df)
            except KeyError:
                panda_dict[tablename] = df

    panda_dict['constants'] = pd.Series(ds.attrs)
    return panda_dict
