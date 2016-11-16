import itertools
import os
import copy
from warnings import warn
from collections import OrderedDict
import numpy as np
import xarray as xr
from itertools import chain

output_meth_0_sep_0 = {
    'pfe_GB': None,
    'pfi_GB': None,
    'gam_GB': None,
    'ome_GB': None,
    'efe_GB': None,
    'efi_GB': None,
    'efi_cm': None,
    'vfi_GB': None,
    'vri_GB': None}

output_meth_0_sep_1 = {
    'dfeITG_GB': None,
    'dfeTEM_GB': None,
    'dfiITG_GB': None,
    'dfiTEM_GB': None,
    'vteITG_GB': None,
    'vteTEM_GB': None,
    'vtiITG_GB': None,
    'vtiTEM_GB': None,
    'vciITG_GB': None,
    'vceITG_GB': None,
    'vceTEM_GB': None,
    'vciTEM_GB': None}

output_meth_1_sep_0 = {
    'cke': None,
    'cki': None,
    'dfe_GB': None,
    'dfi_GB': None,
    'vte_GB': None,
    'vti_GB': None,
    'vce_GB': None,
    'vci_GB': None}

output_meth_1_sep_1 = {
    'efeETG_GB': None,
    'efeITG_GB': None,
    'efeTEM_GB': None,
    'efiITG_GB': None,
    'efiTEM_GB': None,
    'vfiITG_GB': None,
    'vfiTEM_GB': None,
    'vriITG_GB': None,
    'vriTEM_GB': None}

output_meth_2_sep_0 = {
    'ceke': None,
    'ceki': None,
    'chiee_SI': None,
    'chiei_SI': None,
    'vece_SI': None,
    'veci_SI': None,
    'vene_SI': None,
    'veni_SI': None,
    'vere_SI': None,
    'veri_SI': None}

primi_meth_0 = {
    'Lcirce': None,
    'Lcirci': None,
    'Lecirce': None,
    'Lecirci': None,
    'Lepiege': None,
    'Lpiege': None,
    'Lpiegi': None,
    'Lvcirce': None,
    'Lvcirci': None,
    'Lvpiege': None,
    'Lvpiegi': None,
    'ifdsol': None,
    'ijonsolflu': None,
    'imodeshift': None,
    'imodewidth': None,
    'isol': None,
    'isolflu': None,
    'ntor': None,
    'rfdsol': None,
    'rjonsolflu': None,
    'rmodeshift': None,
    'rmodewidth': None,
    'rsol': None,
    'rsolflu': None}

primi_meth_1 = {
    'Lcircgne': None,
    'Lcircgni': None,
    'Lcircgte': None,
    'Lcircgti': None,
    'Lcircgue': None,
    'Lcircgui': None,
    'Lcircce': None,
    'Lcircci': None,
    'Lpiegce': None,
    'Lpiegci': None,
    'Lpieggte': None,
    'Lpieggti': None,
    'Lpieggue': None,
    'Lpieggui': None,
    'Lpieggne': None,
    'Lpieggni': None}

primi_meth_2 = {
    'Lecircce': None,
    'Lecircci': None,
    'Lecircgne': None,
    'Lecircgni': None,
    'Lecircgte': None,
    'Lecircgti': None,
    'Lecircgue': None,
    'Lecircgui': None,
    'Lepiegce': None,
    'Lepiegci': None,
    'Lepieggne': None,
    'Lepieggni': None,
    'Lepieggue': None,
    'Lepieggui': None,
    'Lepiegi': None,
    'Lepieggte': None,
    'Lepieggti': None}

debug_eleclike = {
    'Ane': None,
    'Ate': None,
    'Aupar': None,
    'Autor': None,
    'Machpar': None,
    'Machtor': None,
    'x': None,
    'Zeffx': None,
    'Bo': None,
    'gammaE': None,
    'Nex': None,
    'Nustar': None,
    'qx': None,
    'Ro': None,
    'Rmin': None,
    'smag': None,
    'Tex': None}

debug_ionlike = {
    'Ai': None,
    'Ani': None,
    'Ati': None,
    'Zi': None,
    'ion_type': None,
    'ninorm': None,
    'Tix': None}

debug_single = {
    'dimn': None,
    'dimx': None,
    'nions': None,
    'numsols': None,
    'coll_flag': None,
    'maxpts': None,
    'maxruns': None,
    'R0': None,
    'relacc1': None,
    'relacc2': None,
    'rot_flag': None,
    'separateflux': None,
    'timeout': None}

debug_special = {'kthetarhos': None}
# Some magic to group all datasets. In principe the granularity
# per subset is not needed, but we keep it for legacy purposes
output_subsets = OrderedDict()
output_subsets.update(output_meth_0_sep_0)
output_subsets.update(output_meth_0_sep_1)
output_subsets.update(output_meth_1_sep_0)
output_subsets.update(output_meth_1_sep_1)
output_subsets.update(output_meth_2_sep_0)
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



def determine_sizes(rundir, folder='debug'):
    names = ['dimx', 'dimn', 'nions', 'numsols']
    sizes = OrderedDict()
    for name in names:
        with open(os.path.join(rundir, folder, name + suffix), 'rb') as file:
            data = np.loadtxt(file)
            sizes[name] = int(data)
    return sizes


def convert_debug(sizes, rundir, folder='debug'):
    ds = xr.Dataset()
    dimx, dimn, nions, numsols = sizes.values()
    for name in debug_subsets:
        try:
            dir = os.path.join(rundir, folder)
            basename = name + suffix
            with open(os.path.join(dir, basename), 'rb') as file:
                print ('loading ' + basename.ljust(20) + ' from ' + dir)
                data = np.loadtxt(file)
                if name in ['dimx', 'dimn', 'nions', 'numsols']:
                    continue
                elif name in debug_eleclike:
                    dims=['dimx']
                elif name in debug_ionlike:
                    dims = ['dimx', 'nions']
                elif name in debug_single:
                    dims = None
                elif name in debug_special:
                    dims = ['dimn']
                else:
                    raise Exception('Could not process \'' + name + '\'')
                ds.coords[name] = xr.DataArray(data, dims=dims)
        except FileNotFoundError:
            pass
    ds.coords['numsols'] = xr.DataArray(list(range(0, numsols)), dims='numsols')
    return ds


def convert_output(ds, sizes, rundir, folder='output'):
    dimx, dimn, nions, numsols = sizes.values()
    for name in output_subsets:
        try:
            dir = os.path.join(rundir, folder)
            basename = name + suffix
            with open(os.path.join(dir, basename), 'rb') as file:
                print ('loading ' + basename.ljust(20) + ' from ' + dir)
                data = np.loadtxt(file)
                if name == 'gam_GB' or name == 'ome_GB':
                    data = data.reshape(numsols,dimx,dimn)
                    ds[name] = xr.DataArray(data, dims=['numsols', 'dimx', 'dimn'], name=name).transpose('dimx', 'dimn', 'numsols')
                elif name == 'cke' or name == 'ceke':
                    ds[name] = xr.DataArray(data, dims=['dimx'], name=name)
                elif  name == 'cki' or name == 'ceki' or name == 'ion_type':
                    ds[name] = xr.DataArray(data, dims=['dimx','nions'], name=name)
                elif name == 'efi_cm':
                    data = data.reshape(nions,dimx,dimn)
                    ds[name] = xr.DataArray(data, dims=['nions', 'dimx', 'dimn'], name=name).transpose('dimx', 'dimn', 'nions')
    
                elif name.endswith('_GB') or name.endswith('_SI'):
                    newname = name[:-3]
                    if newname.endswith('ETG') or newname.endswith('ITG') or newname.endswith('TEM'):
                        newname = newname[:-3]
                    if newname.endswith('e'):
                        ds[name] = xr.DataArray(data, dims=['dimx'], name=name)
                    elif newname.endswith('i'):
                        ds[name] = xr.DataArray(data, dims=['dimx','nions'], name=name)
                else:
                    raise Exception('Could not process \'' + name + '\'')
        except FileNotFoundError:
            pass
    return ds


def convert_primitive(ds, sizes, rundir, folder='output/primitive'):
    reshapes = ['rfdsol', 'ifdsol', 'isol', 'rsol']
    dimx, dimn, nions, numsols = sizes.values()
    for name in primi_subsets:
        try:
            dir = os.path.join(rundir, folder)
            basename = name + suffix
            with open(os.path.join(dir, basename), 'rb') as file:
                print ('loading ' + basename.ljust(20) + ' from ' + dir)
                data = np.loadtxt(file)
                if name.endswith('i'):
                    data = data.reshape(numsols,nions,dimx,dimn)
                    ds[name] = xr.DataArray(data, dims=['numsols', 'nions', 'dimx', 'dimn'], name=name).transpose('dimx', 'dimn', 'nions', 'numsols')
                elif name.endswith('e') or name in reshapes:
                    data = data.reshape(numsols,dimx,dimn)
                    ds[name] = xr.DataArray(data, dims=['numsols', 'dimx', 'dimn'], name=name).transpose('dimx', 'dimn', 'numsols')
                else:
                    ds[name] = xr.DataArray(data, dims=['dimx','dimn'], name=name)
        except FileNotFoundError:
            pass
    return ds


def squeeze_coords(ds, dim):
    for name, item in ds.coords.items():
        if dim in item.dims:
            new = np.unique(item)
            if len(new) == 1 and len(item) != 1:
                ds.coords[name] = xr.DataArray(float(new))
            elif 'nions' in item.dims and name != 'nions':
                bool = True
                for i in range(item['nions'].size):
                    bool &= (len(np.unique(item.sel(nions=i).values)) == 1)
                if bool:
                    ds.coords[name] = xr.DataArray(item[0,:].values, coords={'nions': item['nions']})
    return ds


def squeeze_dataset(ds):
    ds.load()
    ## Ni is captured in Zeff
    #try:
    #    ds = ds.drop('ninorm')
    #except ValueError:
    #    pass

    ## Tix is captured in Ti_Te
    #try:
    #    Ti_Te_rel = np.around(ds.Tix / ds.Tex, 5)
    #except ValueError:
    #    pass
    #else:
    #    Ti_Te_rel = Ti_Te_rel.drop('Tix')
    #    ds = ds.drop('Tix')
    #    ds.coords['Ti_Te'] = Ti_Te_rel
    #
    ## Tex is already captured in Nustar
    #try:
    #    ds = ds.drop('Tex')
    #except ValueError:
    #    pass
    
    # Squeeze equal ions 
    for name, item in ds.coords.items():
        bool = True
        if ds['nions'].size > 1 and item.dims == ('dimx', 'nions'):
            for i in range(1, item['nions'].size):
                bool &= (np.allclose(item[:,0], item[:,i]))
            if bool:
                ds[name] = xr.DataArray(item[:,0].values, coords={'dimx': item['dimx']})

    # Squeeze Ane and Ani into An
    if ds['Ane'].equals(ds['Ani']):
        ds.coords['An'] = ds['Ane'].copy()
        ds = ds.drop('Ane')
        ds = ds.drop('Ani')

    # Squeeze Ate and Ati into At
    if ds['Ate'].equals(ds['Ati']):
        ds.coords['At'] = ds['Ate'].copy()
        ds = ds.drop('Ate')
        ds = ds.drop('Ati')

    # Squeeze constant for dimx
    for name, item in ds.coords.items():
        if item.dims == ('dimx',):
            if len(np.unique(item.values)) == 1:
                ds[name] = xr.DataArray(item[0].values)
        elif item.dims == ('dimx', 'nions'):
            for i in range(ds['nions'].size):
                bool &= (len(np.unique(item.sel(nions=i).values)) == 1)
            if bool:
                ds[name] = xr.DataArray(item[0,:].values, coords={'nions': item['nions']})

    # Move metadata to attrs
    for name, item in ds.coords.items():
        if name in debug_single and name not in ds.dims:
            ds.attrs[name] = float(item)
            ds = ds.drop(name)

    # Remove placeholder for kthetarhos
    try:
        ds = ds.swap_dims({'dimn': 'kthetarhos'})
        ds = ds.drop('dimn')
    except ValueError:
        pass
    
    return ds

def unsqueeze_dataset(ds):
    ds.load()
    # Readd placeholder for kthetarhos
    try:
        name = 'kthetarhos'
        ds.coords['dimn'] =xr.DataArray(range(len(ds[name])), coords={name: ds[name]}, name=ds[name].name, attrs=ds[name].attrs, encoding=ds[name].encoding)
        ds = ds.swap_dims({name: 'dimn'})
    except ValueError:
        pass


    # Unsqueeze constants for dimx
    print(ds.dims)
    for name, item in ds.coords.items():
        if 'dimx' not in item.dims and name not in ds.dims and name != 'kthetarhos':
            print(name)
            print(name is not 'kthetarhos')
            print('dimx' not in item.dims and name not in ds.dims and name is not 'kthetarhos')
            ds.drop(name)
            if 'nions' not in item.dims:
                ds.coords[name] = xr.DataArray(np.repeat(item.data, ds['dimx'].size), coords={'dimx': ds['dimx'].data}, name=ds[name].name, attrs=ds[name].attrs, encoding=ds[name].encoding)
            else:
                ds.coords[name] = xr.DataArray(np.repeat(np.atleast_2d(item.data), ds['dimx'].size, axis=0), coords=OrderedDict([('dimx', ds['dimx'].data), ('nions', ds['nions'].data)]), name=ds[name].name, attrs=ds[name].attrs, encoding=ds[name].encoding)

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

from IPython import embed
def remove_dependent_axes(ds):
    # Ni is captured in Zeff
    try:
        ds = ds.reset_coords('ninorm')
    except ValueError:
        pass

    # Tix is captured in Ti_Te
    try:
        Ti_Te_rel = np.around(ds.coords['Tix'] / ds.coords['Tex'], 5)
    except KeyError:
        pass
    else:
        Ti_Te_rel = Ti_Te_rel.drop('Tix')
        ds = ds.reset_coords('Tix')
        ds.coords['Ti_Te'] = Ti_Te_rel

    # Tex is already captured in Nustar
    try:
        ds = ds.reset_coords('Tex')
    except ValueError:
        pass

    return ds


def orthogonalize_dataset(ds):
    ds.load()
    # Move some axes we know depend on eachother to data. We will re-add later
    ds = remove_dependent_axes(ds)
    # Save the non-dimx depending coordinates in a dict. Speeds up code
    tmp_coords = {}
    for name, item in ds.coords.items():
        if 'dimx' not in item.dims and name not in ds.dims:
            tmp_coords[name] = item
            ds = ds.drop(name)

    ortho_dims = [coord for name, coord in ds.coords.items() if name not in ds.dims and 'dimx' in coord.dims]
    new_dims = OrderedDict([(dim.name, np.unique(dim.values)) for dim in ortho_dims])
    new_dims_size  = np.prod([len(dim) for dim in new_dims.values()])
    nest = [((k,), v.drop(ortho_dims[0].name)) for k,v in ds.groupby(ortho_dims[0].name)]
    
    placeholder_arrays = {}
    for name, item in ds.data_vars.items():
        shape = [len(i) for i in new_dims.values()]
        shape += [len(item[x]) for x in item.dims if x != 'dimx']
        placeholder_arrays[name] = np.full(shape, np.nan)
    
    for dim in ortho_dims[1:]:
        newnest = []
        for i, (dimvar, array) in enumerate(nest):
            print (str(i+1) + '/' + str(len(nest)))
            group = array.groupby(dim.name)
            entry = [(dimvar + (k,), v.drop(dim.name)) for k,v in group]
            newnest.extend(entry)
            if dim.name == ortho_dims[-1].name:
                for dimvars, array in entry:
                    if array['dimx'].size > 1:
                        warn('warning! duplicate points! dropping!')
                        array = array.where(array['dimx'] == array['dimx'][0], drop=True)
                    dimindex = ()
                    for dimvar, newdim in zip(dimvars, new_dims.values()):
                        dimindex += (int(np.argwhere(newdim == dimvar)), )

                    for name in ds.data_vars:
                        placeholder_array = placeholder_arrays[name]
                        placeholder_array[dimindex] = array[name].data
        nest = newnest

    # Put the saved coords back
    for name, item in tmp_coords.items():
        ds.coords[name] = item

    dims = copy.deepcopy(new_dims)
    for name in ds.dims:
        if name != 'dimx':
            dims[name] = ds[name]
    newds = xr.Dataset(coords=dims)
    for name, item in ds.data_vars.items():
        dims = list(new_dims.keys())
        dims += [dim for dim in ds[name].dims if dim != 'dimx']
        coords = dict(new_dims)
        for dim in ds[name].dims:
            if dim != 'dimx':
                coords[dim] = ds[dim].data
        newds[name] = xr.DataArray(placeholder_arrays[name], dims=dims,coords=coords)
    
    for attr in ds.attrs:
        newds.attrs[attr] = ds.attrs[attr]
    return newds

def add_dims(ds, newdims):
    newds = xr.Dataset()
    # Put all non-dim coordinates in new ds
    for name, item in ds.coords.items():
        if name not in ds.dims and name not in newdims:
            newds.coords[name] = item

    # Add all dimensions to new ds
    for name in chain(ds.dims.keys(), newdims):
        values = ds[name].values
        if values.size == 1:
            newds[name] = [values]
        else:
            newds[name] = values

    # All new data variables should depend on the new dimensions
    for name, item in ds.data_vars.items():
        newcoords = OrderedDict()
        newitemdims = item.dims + tuple(newdims)
        olddims = item.dims
        for dimname in newdims:
            item = np.expand_dims(item, -1)
            newcoords[dimname] = newds[dimname]
        for dimname in olddims:
            newcoords[dimname] = ds[dimname]

        newds[name] = xr.DataArray(item, dims=newitemdims, coords=newcoords, name=ds[name].name, attrs=ds[name].attrs, encoding=ds[name].encoding)

    # Copy the attributes
    for name, item in ds.attrs.items():
        newds.attrs[name] = item


    return newds

def find_nonmatching_coords(ds1, ds2):
    nonmatching = []
    for name in ds1.coords:
        if np.all(ds1[name] != ds2[name]):
            nonmatching.append(name)

    return nonmatching

def merge_orthogonal(ds1, ds2, datavars=None):
    #ds1.load()
    #ds2.load()
    if not datavars:
        datavars = list(ds1.data_vars.keys())
    nonmatching = find_nonmatching_coords(ds1, ds2)
    for nonmatch in nonmatching:
        if nonmatch not in ds1.dims:
            print('adding dim ' + nonmatch)
            ds1 = add_dims(ds1, nonmatching)
        if nonmatch not in ds2.dims:
            print('adding dim ' + nonmatch)
            ds2 = add_dims(ds2, nonmatching)
    dsnew = xr.Dataset()
    for name in ds1.data_vars:
        if name in datavars:
            print('merging ' + name)
            # Concatenate objects. We need to supply an existing dimension to
            # Prevent the creation of a new dimension
            dsnew[name] = xr.concat((ds1[name], ds2[name]), nonmatching[0], 
                                    coords='all', compat='identical')
            ds1.drop(name)
            ds2.drop(name)
    for nonmatch in nonmatching:
        dsnew = squeeze_coords(dsnew, nonmatch)
    dsnew.attrs = ds1.attrs

    return dsnew

def sort_dims(ds):
    for dim in ds.dims:
        ds = ds.reindex(**{dim: np.sort(ds[dim])})
    return ds
