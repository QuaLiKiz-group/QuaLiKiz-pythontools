import shutil
import os

from scipy.io import loadmat
import numpy as np
from IPython import embed
from collections import OrderedDict
import xarray as xr
import matplotlib.pyplot as plt

from qualikiz_tools.qualikiz_io.outputfiles import convert_debug, convert_output, determine_sizes
from qualikiz_tools.qualikiz_io.inputfiles  import QuaLiKizPlan

mat = loadmat('./testcases_andromede.mat')
cases = {}
for name in mat:
    if not name.startswith('__'):
        casedat = mat[name]
        case = OrderedDict()
        for varname, var in zip(casedat.dtype.names, casedat[0,0]):
            varname = varname.replace('ipf', 'pfi')
            varname = varname.replace('epf', 'pfe')
            varname = varname.replace('eef', 'efe')
            varname = varname.replace('ief', 'efi')
            #if varname.startswith('epf'):
            #    varname[:3] = 'pfe'
            #if varname.startswith('ief'):
            #    varname[:3] = 'efi'
            #if varname.startswith('eef'):
            #    varname[:3] = 'efe'
            case[varname] = var
        #sizes = case['sizes'] = OrderedDict()
        sizes = OrderedDict()
        case['dimx'] =    np.array(case['efe_SI'].shape[0])
        case['dimn'] =    np.array(case['kthetarhos'].shape[0])
        case['nions'] =   np.array(int(case['efi_SI'].shape[0] / case['dimx']))
        case['numsols'] = np.array(int(case['ome_GB'].shape[0] / case['dimx']))

        shutil.rmtree(name, ignore_errors=True)
        os.mkdir(name)
        for varname, var in case.items():
            var.tofile(name + '/' + varname + '.dat', sep=' ')
        ds = xr.Dataset()
        sizes = determine_sizes(name, folder='.')

        ds = convert_debug(sizes, name, folder='.', verbose=True)
        ds = convert_output(ds, sizes, name, folder='.', verbose=True)

        for varname in ['dimx', 'dimn', 'nions']:
            ds.coords[varname] = np.arange(case[varname])

        file = name + '_parameters.json'
        plan = QuaLiKizPlan.from_json(os.path.join('../casefiles', file))
        ds.coords['smag'] = xr.DataArray(plan['scan_dict']['smag'], dims='dimx')
        cases[name] = ds
        ds.to_netcdf(name + '.nc')
        shutil.rmtree(name)
