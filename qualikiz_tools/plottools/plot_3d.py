"""
Copyright Dutch Institute for Fundamental Energy Research (2016-2017)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import warnings
from collections import OrderedDict

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import gridspec, cycler
from mpl_toolkits.mplot3d import Axes3D

from qualikiz_tools.qualikiz_io.outputfiles import squeeze_dataset, orthogonalize_dataset, xarray_to_pandas

try:
    from .discrete_slider import DiscreteSlider
except ModuleNotFoundError:
    from discrete_slider import DiscreteSlider

def build_plot(dataset, scan_dims, flux_type, normalization, instability_tag='', sum_hydrogen=True, drop_non_hydrogen=True, lowwave_boundry=2):
    squeeze = squeeze_dataset(dataset)
    # We need an unsqueezed Zi for hydrogen detection
    if 'nions' not in squeeze['Zi'].dims:
        squeeze.coords['Zi'] = xr.DataArray(np.tile(squeeze['Zi'], (1, len(squeeze['nions']))), dims=['set', 'nions'])
    if 'dimx' not in squeeze['Zi'].dims:
        squeeze.coords['Zi'] = xr.DataArray(np.tile(squeeze['Zi'].data, (len(squeeze['dimx']), 1)), dims=['dimx', 'nions'])
    squeeze = orthogonalize_dataset(squeeze)


    # Prepare dataset
    dfs = xarray_to_pandas(squeeze)
    efelike = dfs[tuple(scan_dims)]
    efilike = dfs[tuple(scan_dims + ['nions'])].unstack(level=('nions'))
    freqlike = dfs[tuple(scan_dims + ['kthetarhos', 'numsols'])]

    # Build plot target names
    target_efelike = ''.join([flux_type, 'e', instability_tag, '_', normalization])
    target_efilike = ''.join([flux_type, 'i', instability_tag, '_', normalization])

    freq_name = 'ome_' + normalization
    grow_name = 'gam_' + normalization

    # Build plot area
    fig = plt.figure()
    gs = gridspec.GridSpec(24, 4, hspace=20, left=0.05, right=0.95, bottom=0.05, top=0.95)
    axes = {
        'flux': plt.subplot(gs[:,:2], projection='3d'),
        'freq_low': plt.subplot(gs[:10,2]),
        'freq_high': plt.subplot(gs[:10,3]),
        'grow_low':    plt.subplot(gs[10:-4,2]),
        'grow_high':   plt.subplot(gs[10:-4,3]),
        'slider0': plt.subplot(gs[-4:-2,2:]),
        'slider1': plt.subplot(gs[-2:,2:])
    }
    flux_colors = plt.get_cmap('tab10').colors
    axes['flux'].set_xlabel(scan_dims[0])
    axes['flux'].set_ylabel(scan_dims[1])
    axes['flux'].set_zlabel(''.join([flux_type, instability_tag, '_', normalization]))
    axes['freq_low'].set_ylabel('freq_low')
    axes['freq_high'].set_ylabel('freq_high')
    axes['grow_low'].set_ylabel('grow_low')
    axes['grow_high'].set_ylabel('grow_high')

    for ax in axes.values():
        ax.ticklabel_format(style='sci', scilimits=(-2, 2), axis='y')

    #freq_ax.set_ylabel(freq_name)
    #grow_ax.set_ylabel(grow_name)

    # Define the event triggered by slider update
    def update_grow(val):
        for type in ['freq', 'grow']:
            for part in ['high', 'low']:
                name = type + '_' + part
                ax = axes[name]
                point = []
                for slider in sliders:
                    point.append(slider.previous_val)
                #first_scan0_val = freqlike_table[name].index.levels[0][0]
                #first_scan1_val = freqlike_table[name].index.levels[1][0]
                #table = freqlike_table[name].loc[first_scan0_val, first_scan1_val].unstack()
                table = freqlike_table[name].loc[tuple(point), :].unstack()
                for (numsol, values), line in zip(table.items(), ax.lines):
                    values = values.replace(0,np.nan)
                    line.set_ydata(values)
                ax.relim()
                ax.autoscale(axis='y')
        fig.canvas.draw_idle()

    # Initialize dimx slider
    sizes = {}
    sliders = []
    for ii, scan_dim in enumerate(scan_dims):
        dim_vals = efilike.index.get_level_values(scan_dim).unique()
        slider = DiscreteSlider(axes['slider' + str(ii)],
                                 scan_dim,
                                 dim_vals[0],
                                 dim_vals[-1],
                                 allowed_vals=dim_vals,
                                 valinit=dim_vals[0])
        slider.on_changed(update_grow)
        sliders.append(slider)

        sizes[scan_dim] = len(dim_vals)


    # Extract part of dataset and plot it
    idx = pd.IndexSlice

    try:
        efelike_table = efelike[[target_efelike]].reset_index()
    except KeyError:
        print('No electron data found for {!s}'.format(target_efelike))
    else:
        X = efelike_table[scan_dims[0]].reshape(sizes[scan_dims[0]], sizes[scan_dims[1]])
        Y = efelike_table[scan_dims[1]].reshape(sizes[scan_dims[0]], sizes[scan_dims[1]])
        Z = efelike_table[target_efelike].reshape(sizes[scan_dims[0]], sizes[scan_dims[1]])
        #efelike_table.plot(x=scan_dim.name, ax=axes['flux'], marker='o')
        axes['flux'].plot_wireframe(X, Y, Z, color=flux_colors[0], label='Zi = -1.0')

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
            hydro_sum = hydrogen.sum(axis='columns').to_frame()

            # Remembed variable and set of hydrogen summation
            hydro_sum.columns = hydrogen.loc[:, (slice(None), slice(0,0))].columns

            # Drop hydrogen atoms from the efilike_table
            efilike_table.loc[:, pd.Index(hydrogen.columns)] = np.nan

            # Add the summed hydrogen to efilike_table
            efilike_table = efilike_table.combine_first(hydro_sum)

        efilike_table.dropna('columns', inplace=True)
        pd.options.mode.chained_assignment = 'warn' # Turn pandas warnings on


        efilike_table = efilike_table.reset_index()
        X = efilike_table[scan_dims[0]].reshape(sizes[scan_dims[0]], sizes[scan_dims[1]])
        Y = efilike_table[scan_dims[1]].reshape(sizes[scan_dims[0]], sizes[scan_dims[1]])
        for ii, col in enumerate(efilike_table[target_efilike]):
            Z = efilike_table[target_efilike][col].reshape(sizes[scan_dims[0]], sizes[scan_dims[1]])
            axes['flux'].plot_wireframe(X, Y, Z, color=flux_colors[ii + 1], label='Zi = ' + str(efilike['Zi'].iloc[0][col]))
    axes['flux'].legend()
        #efilike_table.plot(x=scan_dim.name, ax=axes['flux'], marker='o')

    freqlike_table = {
        'freq_high': freqlike[['ome_' + normalization]].loc[(idx[:,:,lowwave_boundry:,:]),:],
        'grow_high': freqlike[['gam_' + normalization]].loc[(idx[:,:,lowwave_boundry:,:]),:],
        'freq_low':  freqlike[['ome_' + normalization]].loc[(idx[:,:,:lowwave_boundry,:]),:],
        'grow_low':  freqlike[['gam_' + normalization]].loc[(idx[:,:,:lowwave_boundry,:]),:],
    }

    for type in ['freq', 'grow']:
        for part in ['high', 'low']:
            name = type + '_' + part
            first_scan0_val = freqlike_table[name].index.levels[0][0]
            first_scan1_val = freqlike_table[name].index.levels[1][0]
            table = freqlike_table[name].loc[first_scan0_val, first_scan1_val].unstack()
            try:
                table.plot(ax=axes[name], marker='o')
            except TypeError: #Ignore if empty
                pass
            if part == 'low':
                # Sum all dimxs and sets together
                sums = freqlike_table[name].unstack(level=scan_dims + ['numsols']).sum('columns')
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
    ds = xr.open_dataset('./example.nc')
    #ds2 = xr.open_dataset('./mini_mult_iso.nc')

    flux_type = 'ef'
    instability_tag = 'ITG'
    normalization = 'SI'
    build_plot(ds, ['Ati', 'An'], flux_type, normalization, instability_tag)


#embed()
#slider_ax = plt.subplot(gs[1,0])
#kthetarhos = dfs[('kthetarhos',)]['kthetarhos'].values
#slider = DiscreteSlider(slider_ax, 'label', kthetarhos[0], kthetarhos[-1], allowed_vals=kthetarhos, valinit=kthetarhos[0])
