"""
Copyright Dutch Institute for Fundamental Energy Research (2016-2017)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import gridspec, cycler
from collections import OrderedDict
import numpy as np
import pandas as pd
from qualikiz_tools.qualikiz_io.outputfiles import squeeze_dataset, orthogonalize_dataset, xarray_to_pandas
import warnings

try:
    from .discrete_slider import DiscreteSlider
except ModuleNotFoundError:
    from discrete_slider import DiscreteSlider


def determine_scandim(ds):
    scan_dims = [coord for name, coord in ds.coords.items() if name not in ds.dims and 'dimx' in coord.dims and len(np.unique(coord)) > 1]
    #new_dims = OrderedDict([(dim.name, np.unique(dim.values)) for dim in ortho_dims])
    from IPython import embed
    embed()
    if len(scan_dims) == 0:
        print('No scan dim found')
        scan_dim = ds['dimx']
    elif len(scan_dims) == 1:
        scan_dim = scan_dims[0]
        if scan_dim.dims == ('dimx', ):
            pass
        elif scan_dim.dims == ('dimx', 'nions') or scan_dim.dims == ('set', 'dimx', 'nions'):
            can_squeeze = True
            for i in scan_dim['dimx']:
                 unique_vals = np.unique(scan_dim.sel(**{'dimx': i}))
                 unique_vals = unique_vals[~np.isnan(unique_vals)]
                 can_squeeze &= (len(unique_vals) == 1)
            if can_squeeze:
                try:
                    scan_dim = scan_dim.sel(nions=0, set=0)
                except ValueError:
                    scan_dim = scan_dim.sel(nions=0)
            else:
                print('Warning! Ions unsqueezable. Behaviour untested!')
                scan_dim = ds['dimx']
        else:
            print('Scan_dim dims are {!s}. Not sure what to do'.format(scan_dim.dims))
            scan_dim = ds['dimx']

    elif len(scan_dims) > 1:
        print('Warning! More than 1 scanned variable! Behaviour untested!')
        scan_dim = ds['dimx']
    return scan_dim

def change_efeline():
    pass


def build_plot(datasets, flux_type, normalization, instability_tag='', sum_hydrogen=True, drop_non_hydrogen=True, lowwave_boundry=2):
    squeezed = []
    for dataset in datasets:
        squeeze = squeeze_dataset(dataset)
        # We need an unsqueezed Zi for hydrogen detection
        if 'nions' not in squeeze['Zi'].dims:
            squeeze.coords['Zi'] = xr.DataArray(np.tile(squeeze['Zi'], (1, len(squeeze['nions']))), dims=['set', 'nions'])
        if 'dimx' not in squeeze['Zi'].dims:
            squeeze.coords['Zi'] = xr.DataArray([np.tile(squeeze['Zi'].data, (len(squeeze['dimx']), 1))], dims=['set', 'dimx', 'nions'])
        squeezed.append(squeeze)

    try:
        ds = xr.concat(squeezed, dim='set')
    except KeyError:
        raise Exception('Incompatible datasets for simple plotting')


    # Determine scan dimension
    scan_dim_array = determine_scandim(ds)
    scan_dim = scan_dim_array.to_pandas()
    scan_dim.name = scan_dim_array.name

    # Prepare dataset
    dfs = xarray_to_pandas(ds)
    efelike = dfs[('set', 'dimx', )].unstack(level=('set'))
    efilike = dfs[('set', 'dimx', 'nions')].unstack(level=('set', 'nions'))
    freqlike = dfs[('set', 'dimx', 'kthetarhos', 'numsols')].unstack(level=('set'))

    # Build plot target names
    target_efelike = ''.join([flux_type, 'e', instability_tag, '_', normalization])
    target_efilike = ''.join([flux_type, 'i', instability_tag, '_', normalization])

    freq_name = 'ome_' + normalization
    grow_name = 'gam_' + normalization

    # Build plot area
    fig = plt.figure()
    gs = gridspec.GridSpec(22, 4, hspace=20, left=0.05, right=0.95, bottom=0.05, top=0.95)
    axes = {
        'flux': plt.subplot(gs[:,:2]),
        'freq_low': plt.subplot(gs[:10,2]),
        'freq_high': plt.subplot(gs[:10,3]),
        'grow_low':    plt.subplot(gs[10:-2,2]),
        'grow_high':   plt.subplot(gs[10:-2,3]),
        'dimx_slider': plt.subplot(gs[-2:,2:])
    }
    axes['freq_low'].set_ylabel('freq_low')
    axes['freq_high'].set_ylabel('freq_high')
    axes['grow_low'].set_ylabel('grow_low')
    axes['grow_high'].set_ylabel('grow_high')

    for ax in axes.values():
        ax.ticklabel_format(style='sci', scilimits=(-2, 2), axis='y')

    #freq_ax.set_ylabel(freq_name)
    #grow_ax.set_ylabel(grow_name)

    # Initialize dimx slider
    dfs[('dimx', )]['dimx'] = dfs[('dimx', )].index
    dimx = dfs[('dimx', )]['dimx'].values
    dimx_slider = DiscreteSlider(axes['dimx_slider'],
                                 'dimx',
                                 dimx[0],
                                 dimx[-1],
                                 allowed_vals=dimx,
                                 valinit=dimx[0])

    # Define the event triggered by slider update
    def update_grow(val):
        for type in ['freq', 'grow']:
            for part in ['high', 'low']:
                name = type + '_' + part
                ax = axes[name]
                table = freqlike_table[name].loc[val].unstack()
                for (numsol, values), line in zip(table.items(), ax.lines):
                    values = values.replace(0,np.nan)
                    line.set_ydata(values)
                ax.relim()
                ax.autoscale(axis='y')
        fig.canvas.draw_idle()
    dimx_slider.on_changed(update_grow)

    # Extract part of dataset and plot it
    idx = pd.IndexSlice
    try:
        efelike_table = efelike[[target_efelike]].join(scan_dim)
    except KeyError:
        print('No electron data found for {!s}'.format(target_efelike))
    else:
        efelike_table.plot(x=scan_dim.name, ax=axes['flux'], marker='o')

    pd.options.mode.chained_assignment = None # Ignore pandas warnings
    try:
        efilike_table = efilike[[target_efilike]]
    except KeyError:
        print('No ion data found for {!s}'.format(target_efilike))
    else:
        if drop_non_hydrogen:
            non_hydrogen = efilike_table.loc[:,(slice(None), (efilike['Zi'] != 1).all())]

            efilike_table.loc[:, pd.Index(non_hydrogen.columns)] = np.nan

        if sum_hydrogen:
            # Find hydrogen ions
            hydrogen = efilike_table.loc[:,(slice(None), (efilike['Zi'] == 1).all())]
            hydro_sum = hydrogen.sum(axis='columns', level='set')

            # Remembed variable and set of hydrogen summation
            hydro_sum.columns = hydrogen.loc[:, (slice(None), slice(None), slice(0,0))].columns

            # Drop hydrogen atoms from the efilike_table
            efilike_table.loc[:, pd.Index(hydrogen.columns)] = np.nan

            # Add the summed hydrogen to efilike_table
            efilike_table = efilike_table.combine_first(hydro_sum)

        efilike_table.dropna('columns', inplace=True)
        pd.options.mode.chained_assignment = 'warn' # Turn pandas warnings on


        efilike_table = efilike_table.join(scan_dim)
        efilike_table.plot(x=scan_dim.name, ax=axes['flux'], marker='o')

    freqlike_table = {
        'freq_high': freqlike['ome_' + normalization].loc[(idx[:,lowwave_boundry:,:]),:],
        'grow_high': freqlike['gam_' + normalization].loc[(idx[:,lowwave_boundry:,:]),:],
        'freq_low':  freqlike['ome_' + normalization].loc[(idx[:,:lowwave_boundry,:]),:],
        'grow_low':  freqlike['gam_' + normalization].loc[(idx[:,:lowwave_boundry,:]),:],
    }

    for type in ['freq', 'grow']:
        for part in ['high', 'low']:
            name = type + '_' + part
            table = freqlike_table[name].loc[0].unstack()
            try:
                table.plot(ax=axes[name], marker='o')
            except TypeError: #Ignore if empty
                pass
            if part == 'low':
                # Sum all dimxs and sets together
                sums = freqlike_table[name].unstack(level=['dimx', 'numsols']).sum('columns')
                kthetarhos_max = sums.ne(0)[::-1].argmax()
                axes[name].set_xlim(left=0, right=kthetarhos_max)

    #freq_table = freqlike[freq_name].loc[0].unstack()
    #freq_low_table = freq_table[freq_table.index<2]
    #freq_high_table = freq_table[freq_table.index>=2]
    #freq_low_table.plot(ax=freq_low_ax, marker='o')
    #freq_high_table.plot(ax=freq_high_ax, marker='o')
    #embed()

    plt.show()

if __name__ == '__main__':
    ds = xr.open_dataset('./mini.nc')
    ds2 = xr.open_dataset('./mini_mult_iso.nc')

    flux_type = 'ef'
    instability_tag = 'ITG'
    normalization = 'SI'
    build_plot([ds, ds2], flux_type, normalization, instability_tag)


#embed()
#slider_ax = plt.subplot(gs[1,0])
#kthetarhos = dfs[('kthetarhos',)]['kthetarhos'].values
#slider = DiscreteSlider(slider_ax, 'label', kthetarhos[0], kthetarhos[-1], allowed_vals=kthetarhos, valinit=kthetarhos[0])
