import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sc
import os
from matplotlib.widgets import Slider
import time
from cycler import cycler
from collections import OrderedDict
from math import ceil

import matplotlib.gridspec as gridspec
from IPython import embed

def takespread(sequence, num):
    length = float(len(sequence))
    for i in range(num):
        yield sequence[int(ceil(i * length / num))]

def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return array[idx]

starttime = time.time()

ds = xr.open_dataset('output.nc')
rundir = 'runs/x0.15Ti_Te_rel1.0Zeff1.0Nustar0.001/smag1.0'
suffix = '.dat'

xaxis_name = 'qx'
xaxis_name = 'An'
y_axis = 'efi_GB'

scan_dims = [name for name in ds.dims if name not in ['nions', 'numsols', 'dimn'] and name != xaxis_name]

slider_dict = OrderedDict()
numslider = 0
for name in scan_dims:
    slider_dict[name] = []
    for i in range(0,len(ds[name].shape)):
        slider_dict[name].append({'posvals': np.unique(ds[name].values)})
        numslider += 1
print ('analysed sliders at t=' + str(time.time() - starttime))

def update(val):
    starttime = time.time()
    sel_dict = {}
    for name, sliders in slider_dict.items():
        sel_dict[name] = sliders[0]['slider'].val

    slice_ = ds.sel(method='nearest', **sel_dict)
    for name, sliders in slider_dict.items():
        sliders[0]['dispval'].set_text('{0:.3g}'.format(float(slice_[name])))

    print ('Slicing took              ' + str(time.time() - starttime) + ' s')
    starttime = time.time()

    #slice_ = ds.where(bool, drop=True)
    x = slice_[xaxis_name]
    y = slice_[y_axis]
    mainax.lines.clear() 
    mainax.plot(x.data, y.data, marker='o', color='blue')

    print ('Plotting variable took    ' + str(time.time() - starttime) + ' s')
    starttime = time.time()

    growax.lines.clear() 
    freqax.lines.clear()
    slice_gam = slice_['gam_GB'].stack(sol=('numsols','dimn'))
    slice_gam = slice_gam.where(slice_gam!= 0).dropna(xaxis_name, how='all')
    slice_gam = slice_gam.dropna('sol', how='all')
    slice_ome = slice_['ome_GB'].stack(sol=('numsols','dimn'))
    slice_ome = slice_ome.where(slice_ome!= 0).dropna(xaxis_name, how='all')
    slice_ome = slice_ome.dropna('sol', how='all')
    print ('Slicing growthrates/few   ' + str(time.time() - starttime) + ' s')
    starttime = time.time()

    color = takespread(plt.get_cmap('plasma').colors, slice_.dims['dimn'])
    growax.set_prop_cycle(cycler('color', color))
    growax.plot(np.repeat(np.atleast_2d(slice_gam[xaxis_name]),slice_gam['sol'].size,axis=0).T, slice_gam, marker='o')
    color = takespread(plt.get_cmap('plasma').colors, slice_.dims['dimn'])
    freqax.set_prop_cycle(cycler('color', color))
    freqax.plot(np.repeat(np.atleast_2d(slice_ome[xaxis_name]),slice_ome['sol'].size,axis=0).T, slice_ome, marker='o')

    print ('Plotting growthrates/few  ' + str(time.time() - starttime) + ' s')
    mainax.figure.canvas.draw()


width = 14
fig = plt.figure()
fig.set_tight_layout(True)
gs = gridspec.GridSpec(numslider*2 + 1,width, )
slidenr = 0
mainplot = gs[:numslider,:]
mainax = plt.subplot(gs[:numslider,:int((width-2)/3)])
growax = plt.subplot(gs[:numslider,int((width-2)/3):int(2*(width-2)/3)])
freqax = plt.subplot(gs[:numslider,int(2*(width-2)/3):width-2])
mainax.set_xlabel(xaxis_name)
mainax.set_ylabel(y_axis)
growax.set_xlabel(xaxis_name)
growax.set_ylabel('gam_GB')
freqax.set_xlabel(xaxis_name)
freqax.set_ylabel('ome_GB')
tableax = plt.subplot(gs[:numslider,-2:])
pos_scans = [
'Ati',
'Ate',
'Ane',
'qx',
'smag',
'x',
'Ti/Te',
'Zeffx',
'Nustar']
tab = {}
cellText = []

for name, value in ds.attrs.items():
    if name in pos_scans:
        tab[name] = value
        cellText.append([name, '{0:.1g}'.format(value)])
tableax.axis('off')
table = tableax.table(cellText=cellText, loc='center')
#table.set_fontsize(matplotlib.rcParams['font.size'])
#table.auto_set_font_size(False)

plt.xlabel(xaxis_name)
plt.ylabel(y_axis)
print ('initialized plots at t=' + str(time.time() - starttime))
for name, slider_list in slider_dict.items():
    for i, slider_entry in enumerate(slider_list):
        slidenr +=1
        ax = plt.subplot(gs[numslider+slidenr, :width-2])
        posvals = slider_entry['posvals']
        if len(slider_list) > 1:
            label = name+str(i)
        else:
            label = name
        slider = Slider(ax, label, np.min(posvals), np.max(posvals), valinit=find_nearest(posvals, np.median(posvals)))
        slider.valtext.set_visible(False)
        slider.on_changed(update)
        slider_entry['slider'] = slider
        ax = plt.subplot(gs[numslider+slidenr, -2:], frameon=False)
        ax.axis('off')
        dispval = ax.text(0.5,0.5,slider.val)
        slider_entry['dispval'] = dispval
print ('build sliders at t=' + str(time.time() - starttime))

update('')
print ('plotted at t=' + str(time.time() - starttime))
#fig = plt.figure()
#axes = []
#import itertools
#plot_dims = scan_dims + [xaxis_name]
#outer_grid = gridspec.GridSpec(4, 4, wspace=0.0, hspace=0.0)
#row_dim = plot_dims[2]
#col_dim = plot_dims[3]
#num_row_bins = 4
#num_col_bins = 4
#row_bins = ds.groupby_bins(row_dim, num_row_bins)
#bins = []
#for __, row_bin in row_bins:
#    bins.append(row_bin.groupby_bins(col_dim, num_col_bins))
##col_bins = ds.groupby_bins(col_dim, num_col_bins)
#outer_grid = gridspec.GridSpec(num_row_bins, num_col_bins)
#ylim = [ds[y_axis].min(), ds[y_axis].max()]
#x = ds[plot_dims[0]]
#
#
#for i, bin in enumerate(bins):
#    for j, (__, el) in enumerate(bin):
#        ax = plt.Subplot(fig, outer_grid[i*num_col_bins+j])
#        y = el[y_axis]
#        for l in ds[plot_dims[1]]:
#            y = el[y_axis].sel(**{plot_dims[1]: l}).mean(dim=[col_dim, row_dim])
#            ax.plot(x, y)
#        fig.add_subplot(ax)
#
#    sel_dict = {}

plt.show()
