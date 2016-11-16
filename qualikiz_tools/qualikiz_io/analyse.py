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

ds = xr.open_dataset('runs/Zeff1.7epsilon0.15Nustar0.01Ti_Te_rel1.33.nc')
ds = xr.open_dataset('runs/Zeff1.3epsilon0.15Nustar1e-05Ti_Te_rel0.75.nc')

xaxis_name = 'Ate'
y_axis = 'efi_GB'

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
def update(val):
    starttime = time.time()
    sel_dict = {}
    for name, sliders in slider_dict.items():
        if name != xaxis_name:
            sel_dict[name] = sliders[0]['slider'].val
    global slice_
    slice_new = ds.sel(method='nearest', **sel_dict)
    if not slice_.equals(slice_new):
        slice_ = slice_new
    else:
        return
    for name, sliders in slider_dict.items():
        if name != xaxis_name:
            sliders[0]['dispval'].set_text('{0:.3g}'.format(float(slice_[name])))

    print ('Slicing took              ' + str(time.time() - starttime) + ' s')
    starttime = time.time()

    #slice_ = ds.where(bool, drop=True)
    x = slice_[xaxis_name]
    y = slice_[y_axis]
    elec_y_axis = y_axis[:2] + 'e' + y_axis[-3:]
    mainax.lines.clear() 
    mainax.set_prop_cycle(cycler('color', [plt.cm.prism(i) for i in np.linspace(0, 1, len(ds['nions']) + 1)]))
    mainax.plot(x.data, slice_[elec_y_axis], marker='o')
    mainax.plot(x.data, y.data, marker='o')

    print ('Plotting variable took    ' + str(time.time() - starttime) + ' s')

    growax.lines.clear() 
    freqax.lines.clear()
    for numsol in slice_['numsols']:
        starttime = time.time()
        slice_gam = slice_['gam_GB'].sel(numsols=numsol)
        #gamy = slice_gam.where(slice_gam!=0)
        gamy = slice_gam
        gamx, yv = np.meshgrid(slice_gam['kthetarhos'], slice_gam['An'])

        slice_ome = slice_['ome_GB'].sel(numsols=numsol)
        #omey = slice_ome.where(slice_ome!=0)
        omey = slice_ome
        omex, yv = np.meshgrid(slice_ome['kthetarhos'], slice_ome['An'])
        print ('Slicing growthrates/few   ' + str(time.time() - starttime) + ' s')

        #slice_gam = slice_['gam_GB'].stack(sol=('numsols','kthetarhos'))
        #slice_gam = slice_gam.where(slice_gam!= 0).dropna(xaxis_name, how='all')
        #slice_gam = slice_gam.dropna('sol', how='all')
        #slice_ome = slice_['ome_GB'].stack(sol=('numsols','kthetarhos'))
        #slice_ome = slice_ome.where(slice_ome!= 0).dropna(xaxis_name, how='all')
        #slice_ome = slice_ome.dropna('sol', how='all')
        starttime = time.time()

        color = takespread(plt.get_cmap('plasma').colors, slice_.dims[xaxis_name])
        growax.set_prop_cycle(cycler('color', color))
        growax.loglog(gamx.T, gamy.T)

        color = takespread(plt.get_cmap('plasma').colors, slice_.dims[xaxis_name])
        freqax.set_prop_cycle(cycler('color', color))
        freqax.loglog(omex.T, omey.T)

    print ('Plotting growthrates/few  ' + str(time.time() - starttime) + ' s')
    mainax.figure.canvas.draw()

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
    mainax.set_xlabel(xaxis_name)
    update('')
    mainax.relim()      # make sure all the data fits
    mainax.autoscale()  # auto-scale
    mainax.figure.canvas.draw()

            

width = 14
fig = plt.figure()
fig.set_tight_layout(True)
gs = gridspec.GridSpec(numslider*4 + 1,width)
slidenr = 0
#mainplot = gs[:numslider*2,:]
mainax = plt.subplot(gs[:numslider*2,:int((width-2)/3)])
growax = plt.subplot(gs[:numslider*2,int((width-2)/3):int(2*(width-2)/3)])
freqax = plt.subplot(gs[:numslider*2,int(2*(width-2)/3):width-2])
mainax.set_xlabel(xaxis_name)
mainax.set_ylabel(y_axis)
growax.set_xlabel('kthetarhos')
growax.set_ylabel('gam_GB')
freqax.set_xlabel('kthetarhos')
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

for name, value in ds.coords.items():
    if name in pos_scans and name not in slider_dict:
        tab[name] = value
        cellText.append([name, '{0:.1g}'.format(float(value))])
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
        ax = plt.subplot(gs[2*numslider+2*slidenr-1:2*numslider+2*slidenr, 2:width-2])
        print(numslider+slidenr, width-2)
        posvals = slider_entry['posvals']
        if len(slider_list) > 1:
            label = name+str(i)
        else:
            label = name
        slider = Slider(ax, '', np.min(posvals), np.max(posvals), valinit=find_nearest(posvals, np.median(posvals)))
        slider.valtext.set_visible(False)
        slider.on_changed(update)
        if name == xaxis_name:
            slider.poly.set_color('green')
            slider.active = False
        slider_entry['slider'] = slider
        ax = plt.subplot(gs[2*numslider+2*slidenr-1:2*numslider+2*slidenr, -2:], frameon=False)
        ax.axis('off')
        dispval = ax.text(0.5,0.5,slider.val)
        slider_entry['dispval'] = dispval
        ax = plt.subplot(gs[2*numslider+2*slidenr-1:2*numslider+2*slidenr, :2])
        but = Button(ax, label, color='0.5')
        but.on_clicked(swap_x)
        slider_entry['button'] = but
print ('build sliders at t=' + str(time.time() - starttime))

fakelines = []
#mainax.set_prop_cycle(cycler('color', plt.get_cmap('Paired')))
mainax.set_prop_cycle(cycler('color', [plt.cm.prism(i) for i in np.linspace(0, 1, len(ds['nions']) + 1)]))
for i in range(len(ds['nions']) + 1):
    fakelines.extend(mainax.plot([],[]))

names = ['elec']
names.extend(['A = ' + str(Ai.data) for Ai in ds['Ai']])
mainax.legend(fakelines, names, loc='upper left', fontsize='small')
update('')
print ('plotted at t=' + str(time.time() - starttime))
plt.show()
