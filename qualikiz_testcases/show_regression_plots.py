import sys
import os
import inspect
import copy
from collections import OrderedDict

import numpy as np
import xarray as xr
import pandas as pd
from IPython import embed
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from qualikiz_tools.machine_specific.bash import Run, Batch
from qualikiz_tools.qualikiz_io.inputfiles import QuaLiKizXpoint, QuaLiKizPlan, Electron, Ion, IonList

markers = ['v', '^', '<', '>']
from itertools import cycle

cases = ['v2.4.3', 'HEAD']
fluxes = ['ef', 'pf', 'vf', 'df', 'vt', 'vr', 'vc', 'chie', 'ven', 'ver', 'vec']
scandim = 'smag'
dss_rot = {case: xr.open_dataset(os.path.join(case, 'rot.nc')) for case in cases}
dss_norot = {case: xr.open_dataset(os.path.join(case, 'norot.nc')) for case in cases}
pdf =  PdfPages('regression.pdf')
for rotnorot, dss in zip(['norot', 'rot'], [dss_norot, dss_rot]):
    for flux in fluxes:
        print('plotting', rotnorot, flux)
        for ds_name, ds in dss_rot.items():
            if flux in ['vf', 'vr', 'ver']:
                subds = ds[[flux + 'i_GB']]
            else:
                subds = ds[[flux + 'e_GB', flux + 'i_GB']]
            #subds.reset_coords(scandim, inplace=True)
            subds = subds.drop([coord for coord in subds.coords if coord not in subds.dims])
            subdf = subds.to_dataframe()
            subdf.columns = [col + '_' + ds_name for col in subdf.columns]
            try:
                df = df.join(subdf)
            except NameError:
                df = subdf
        df = pd.merge(df, ds[scandim].to_series().to_frame(), left_on='dimx', right_on='dimx')
        df.set_index(scandim, inplace=True)
        fig, ax = plt.subplots()
        for name, marker in zip(df.columns, cycle(markers)):
            ax.plot(df.index, df[name], marker=marker, label=name)
        ax.set_xlabel(scandim)
        ax.set_ylabel('[GB]')
        ax.legend()
        ax.set_title(rotnorot + ' ' + flux + '_GB')
        pdf.savefig(fig)
        plt.close(fig)
        del df
pdf.close()
print('Done!')
