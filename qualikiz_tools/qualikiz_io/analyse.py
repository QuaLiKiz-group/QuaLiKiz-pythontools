"""
Copyright Dutch Institute for Fundamental Energy Research (2016)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sc
import os
from matplotlib.widgets import Slider, Button
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

ds = xr.open_dataset('runs/Zeff1.0.compressed.nc')



scan_dims = [name for name in ds.dims if name not in ['nions', 'numsols', 'kthetarhos']]

slider_dict = OrderedDict()
numslider = 0
for name in scan_dims:
    slider_dict[name] = []
    for i in range(0,len(ds[name].shape)):
        slider_dict[name].append({'posvals': np.unique(ds[name].values)})
        numslider += 1
print ('analysed sliders at t=' + str(time.time() - starttime))

slice_ = xr.Dataset()
def plot_subslice(ax, subslice):
        y = subslice
        x, yv = np.meshgrid(subslice['kthetarhos'], subslice[xaxis_name])

        color = takespread(plt.get_cmap('plasma').colors, slice_.dims[xaxis_name])
        ax.set_prop_cycle(cycler('color', color))
        ax.plot(x.T, y.T, marker='o')
    
def update(val):
    starttime = time.time()
    sel_dict = {}
    for name, sliders in slider_dict.items():
        if name != xaxis_name:
            if name == 'Nustar':
                sel_dict[name] = 10**sliders[0]['slider'].val
            else:
                sel_dict[name] = sliders[0]['slider'].val
            
    global slice_
    slice_new = ds.sel(method='nearest', **sel_dict)
    if not slice_.equals(slice_new):
        slice_ = slice_new
    else:
        return
    for name, sliders in slider_dict.items():
        if name != xaxis_name:
            if name == 'Nustar':
                sliders[0]['dispval'].set_text('{0:.1e}'.format(10**np.log10(float(slice_[name]))))
            else:
                sliders[0]['dispval'].set_text('{0:.3g}'.format(float(slice_[name])))

    print ('Slicing took              ' + str(time.time() - starttime) + ' s')
    starttime = time.time()

    x = slice_[xaxis_name]
    y = np.vstack([np.atleast_2d(slice_['efe_GB']), slice_['efi_GB'].T]).T
    efax.lines.clear() 
    efax.set_prop_cycle(cycler('color', [plt.cm.prism(i) for i in np.linspace(0, 1, len(ds['nions']) + 1)]))
    efax.plot(x, y, marker='o')
    
    
    x = slice_[xaxis_name]
    y = np.vstack([np.atleast_2d(slice_['pfe_GB']), slice_['pfi_GB'].T]).T
    pfax.lines.clear() 
    pfax.set_prop_cycle(cycler('color', [plt.cm.prism(i) for i in np.linspace(0, 1, len(ds['nions']) + 1)]))
    pfax.plot(x, y, marker='o')


    print ('Plotting variable took    ' + str(time.time() - starttime) + ' s')

    gamlowax.lines.clear() 
    gamhighax.lines.clear() 
    omelowax.lines.clear() 
    omehighax.lines.clear() 
    for numsol in slice_['numsols']:
        subslice = slice_['gam_GB'].sel(numsols=numsol, kthetarhos=slice(None, kthetarhos_cutoff))
        subslice = subslice.where(subslice != 0)
        plot_subslice(gamlowax, subslice)
        subslice = slice_['gam_GB'].sel(numsols=numsol, kthetarhos=slice(kthetarhos_cutoff, None))
        subslice = subslice.where(subslice != 0)
        plot_subslice(gamhighax, subslice)
        subslice = slice_['ome_GB'].sel(numsols=numsol, kthetarhos=slice(None, kthetarhos_cutoff))
        subslice = subslice.where(subslice != 0)
        plot_subslice(omelowax, subslice)
        subslice = slice_['ome_GB'].sel(numsols=numsol, kthetarhos=slice(kthetarhos_cutoff, None))
        subslice = subslice.where(subslice != 0)
        plot_subslice(omehighax, subslice)
        #omey = slice_ome.where(slice_ome!=0)

    print ('Plotting growthrates/few  ' + str(time.time() - starttime) + ' s')
    efax.figure.canvas.draw()

def swap_x(event):
    for name, slider_list in slider_dict.items():
        for i, slider_entry in enumerate(slider_list):
            if slider_entry['button'].ax == event.inaxes:
                clicked_name = name
                clicked_num = i
                slider_entry['slider'].poly.set_color('green')
                slider_entry['slider'].active = False
            else:
                slider_entry['slider'].poly.set_color('blue')
                slider_entry['slider'].active = True
    global xaxis_name
    xaxis_name = clicked_name
    efax.set_xlabel(xaxis_name)
    pfax.set_xlabel(xaxis_name)
    update('')
    efax.relim()      # make sure all the data fits
    efax.autoscale()  # auto-scale
    efax.figure.canvas.draw()

            

width = 14
fig = plt.figure()
fig.set_tight_layout(True)
gs = gridspec.GridSpec(2, 1)
gs_plots = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=gs[0])
gs_bars = gridspec.GridSpecFromSubplotSpec(numslider, width, subplot_spec=gs[1])
gs_omegam = gridspec.GridSpecFromSubplotSpec(2, 2, gs_plots[2])
slidenr = 0
#mainplot = gs[:numslider*2,:]
efax = plt.subplot(gs_plots[0])
pfax = plt.subplot(gs_plots[1])
gamlowax = plt.subplot(gs_omegam[0,0])
gamhighax = plt.subplot(gs_omegam[0,1])
omelowax = plt.subplot(gs_omegam[1,0])
omehighax = plt.subplot(gs_omegam[1,1])
xaxis_name = 'Ate'
efax.set_xlabel(xaxis_name)
efax.set_ylabel('Energy Flux [GB]')
pfax.set_xlabel(xaxis_name)
pfax.set_ylabel('Particle Flux [GB]')

kthetarhos_cutoff = 1
gamlowax.set_ylabel('gam_GB')
gamlowax.set_xlim([0, kthetarhos_cutoff])
gamhighax.set_xlim([kthetarhos_cutoff, 1.05 * np.max(ds['kthetarhos'])])
omelowax.set_ylabel('ome_GB')
omelowax.set_xlabel('kthetarhos')
omelowax.set_xlim([0, kthetarhos_cutoff])
omehighax.set_xlabel('kthetarhos')
omehighax.set_xlim([kthetarhos_cutoff, 1.05 * np.max(ds['kthetarhos'])])



#tableax = plt.subplot(gs[:numslider,-2:])
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

#for name, value in ds.coords.items():
#    if name in pos_scans and name not in slider_dict:
#        tab[name] = value
#        cellText.append([name, '{0:.1g}'.format(float(value))])
#tableax.axis('off')
#table = tableax.table(cellText=cellText, loc='center')
#table.set_fontsize(matplotlib.rcParams['font.size'])
#table.auto_set_font_size(False)

print ('initialized plots at t=' + str(time.time() - starttime))
for name, slider_list in slider_dict.items():
    for i, slider_entry in enumerate(slider_list):
        slidenr +=1
        ax = plt.subplot(gs_bars[slidenr - 1, 2:-1])
        print(numslider+slidenr, width-2)
        posvals = slider_entry['posvals']
        if len(slider_list) > 1:
            label = name+str(i)
        else:
            label = name
        if name == 'Nustar':
            slider = Slider(ax, '', np.log10(np.min(posvals)), np.log10(np.max(posvals)), valinit=np.log10(find_nearest(posvals, np.median(posvals))))
        else:
            slider = Slider(ax, '', np.min(posvals), np.max(posvals), valinit=find_nearest(posvals, np.median(posvals)))
        for posval in posvals:
            if name == 'Nustar':
                slider.ax.plot([np.log10(posval), np.log10(posval)], [0, 1], color='r')
            else:
                slider.ax.plot([posval, posval], [0, 1], color='r')

        slider.valtext.set_visible(False)
        slider.on_changed(update)
        if name == xaxis_name:
            slider.poly.set_color('green')
            slider.active = False
        slider_entry['slider'] = slider
        ax = plt.subplot(gs_bars[slidenr - 1, -1], frameon=False)
        ax.axis('off')
        dispval = ax.text(0.5,0.5,slider.val)
        slider_entry['dispval'] = dispval
        ax = plt.subplot(gs_bars[slidenr - 1, :2])
        but = Button(ax, label, color='0.5')
        but.on_clicked(swap_x)
        slider_entry['button'] = but
print ('build sliders at t=' + str(time.time() - starttime))

fakelines = []
#mainax.set_prop_cycle(cycler('color', plt.get_cmap('Paired')))
efax.set_prop_cycle(cycler('color', [plt.cm.prism(i) for i in np.linspace(0, 1, len(ds['nions']) + 1)]))
for i in range(len(ds['nions']) + 1):
    fakelines.extend(efax.plot([],[]))

names = ['elec']
names.extend(['A = ' + str(Ai.data) for Ai in ds['Ai']])
efax.legend(fakelines, names, loc='upper left', fontsize='small')
pfax.legend(fakelines, names, loc='upper left', fontsize='small')
update('')
print ('plotted at t=' + str(time.time() - starttime))
plt.show()
