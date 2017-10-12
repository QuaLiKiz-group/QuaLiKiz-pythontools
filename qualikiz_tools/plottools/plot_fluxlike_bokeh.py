import xarray as xr
from IPython import embed
import matplotlib.pyplot as plt
from matplotlib import gridspec, cycler
from collections import OrderedDict
import numpy as np
import pandas as pd
from qualikiz_tools.qualikiz_io.outputfiles import squeeze_dataset, orthogonalize_dataset, xarray_to_pandas
from bokeh.io import output_file, show
from bokeh.plotting import figure
from bokeh.layouts import widgetbox,row, column
from bokeh.models.widgets import Dropdown
from bokeh.models import ColumnDataSource, CustomJS


ds = xr.open_dataset('./mini.nc')
ds = squeeze_dataset(ds)

def determine_scandim(ds):
    scan_dims = [coord for name, coord in ds.coords.items() if name not in ds.dims and 'dimx' in coord.dims]
    #new_dims = OrderedDict([(dim.name, np.unique(dim.values)) for dim in ortho_dims])
    if len(scan_dims) == 0:
        print('No scan dim found')
    elif len(scan_dims) == 1:
        scan_dim = scan_dims[0]
        if scan_dim.dims == ('dimx', ):
            pass
        elif scan_dim.dims == ('dimx', 'nions'):
            can_squeeze = True
            for i in scan_dim['dimx']:
                 can_squeeze &= (len(np.unique(scan_dim.sel(**{'dimx': i}))) == 1)
            if can_squeeze:
                scan_dim = scan_dim.sel(nions=0)
            else:
                print('Warning! More than 1 scanned variable! Behaviour untested!')
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


dfs = xarray_to_pandas(ds)
efilike = dfs[('dimx', 'nions')].unstack()
efelike = dfs[('dimx', )]

efe_select = Dropdown(menu=list(zip(efelike.columns, efelike.columns)))
#efi_lines = Dropdown(menu=list(zip(efilike.columns, efilike.columns)))
efe_source = ColumnDataSource(efelike)

fluxplot = figure(title="Full data set", y_axis_label='HI')
efe_line = fluxplot.line(x='dimx', y='efeETG_GB', source=efe_source)
efelike_js = """
             efe_line.glyph.y.field = cb_obj.value
             efe_label = cb_obj.value
             efe_source.change.emit()
             """
efe_label = fluxplot.yaxis[0].axis_label
callback_efelike = CustomJS(args=dict(efe_line=efe_line, efe_source=efe_source, fluxplot=fluxplot, efe_label=efe_label), code=efelike_js)
efe_select.js_on_click(callback_efelike)


show(row(widgetbox(efe_select), fluxplot))


#scan_dim = determine_scandim(ds)

#flux_ax.plot(ds['dimx'], ds[target])
#flux_ax.plot(ds[target2].dimx, ds[target2])
#flux_ax.set_xlabel(scan_dim.name)
#flux_ax.set_ylabel(ds[target].name)

embed()
