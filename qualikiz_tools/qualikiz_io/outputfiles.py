import itertools
import os
import copy
from warnings import warn
from collections import OrderedDict
import numpy as np
import xarray as xr

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
ds = xr.Dataset()

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


def squeeze_dataset(ds, sizes):
    dimx, dimn, nions, numsols = sizes.values()
    # Ni is captured in Zeff
    ds = ds.drop('ninorm')

    # Tix is captured in Ti_Te
    Ti_Te_rel = ds.Tix / ds.Tex
    Ti_Te_rel = Ti_Te_rel.drop('Tix')
    ds = ds.drop('Tix')
    ds.coords['Ti_Te'] = Ti_Te_rel
    
    # Tex is already captured in Nustar
    ds = ds.drop('Tex')
    
    # Squeeze equal ions 
    for name, item in ds.items():
        bool = True
        if nions > 1 and item.dims == ('dimx', 'nions'):
            for i in range(1, nions - 1):
                bool &= (np.allclose(item[:,0], item[:,i]))
            if bool:
                ds[name] = xr.DataArray(item[:,0].values, coords={'dimx': item['dimx']})

    # Squeeze Ane and Ani into An
    if ds['Ane'].equals(ds['Ani']):
        ds.coords['An'] = ds['Ane'].copy()
        ds = ds.drop('Ane')
        ds = ds.drop('Ani')

    # Squeeze dimxs
    for name, item in ds.coords.items():
        bool = True
        if item.dims == ('dimx', 'nions'):
            for i in range(nions):
                bool &= (len(np.unique(item[:, i].values)) == 1)
            if bool:
                ds[name] = xr.DataArray(item[0,:].values, coords={'nions': item['nions']})

    for name, item in ds.coords.items():
        if item.dims == ('dimx',):
            if len(np.unique(item.values)) == 1:
                ds[name] = xr.DataArray(item[0].values)

    # Store metadata in attrs
    for name, item in ds.coords.items():
        if item.shape == ():
            ds.attrs[name] = float(item)
            ds = ds.drop(name)
    
    return ds


def orthogonalize_dataset(ds):
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
        print ('starting ' + dim.name)
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

    dims = copy.deepcopy(new_dims)
    for name in ds.dims:
        if name != 'dimx':
            dims[name] = ds[name]
    newds = xr.Dataset(coords=dims)
    for name, item in ds.data_vars.items():
        dims = list(new_dims.keys())
        dims += [x for x in ds[name].dims if x != 'dimx'] 
        newds[name] = xr.DataArray(placeholder_arrays[name], dims=dims,coords=new_dims)
    
    for attr in ds.attrs:
        newds.attrs[attr] = ds.attrs[attr]
    return newds
