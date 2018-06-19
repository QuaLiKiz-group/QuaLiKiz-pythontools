import sys
import os
import inspect
import copy
from collections import OrderedDict

import numpy as np
from IPython import embed

from qualikiz_tools.machine_specific.bash import Run, Batch
from qualikiz_tools.qualikiz_io.inputfiles import QuaLiKizXpoint, QuaLiKizPlan, Electron, Ion, IonList

# from http://gs2.sourceforge.net/PMP/itg.html
# The cyclon base-case parameters are as follows:
#R/L_Ti = 6.9
#R/L_ne = 2.2
#r/R = 0.18
#q = 1.4
#s_hat = 0.8
#alpha=0
#T_i/T_e = 1.0
#Z_eff = 1.0
#beta = 0.0
#nu* = 0.0

## Load the default parameters.json
qualikiz_plan_base = QuaLiKizPlan.from_json('./parameters.json')
xpoint = qualikiz_plan_base['xpoint_base']


# Some values that depend on other values
xpoint['x'] = 0.18 * xpoint['R0'] / xpoint['Rmin']
xpoint['rho'] = xpoint['x']

# And some options we might want to mess with
xpoint['phys_meth'] = 2
xpoint['rot_flag'] = 1
xpoint['verbose'] = 1
xpoint['separateflux'] = 1

# Set some options just in case the defaults change
xpoint['set_qn_normni'] = False
xpoint['set_qn_An'] = False
xpoint['check_qn'] = True
xpoint['x_eq_rho'] = False
xpoint['recalc_Nustar'] = False
xpoint['recalc_Ti_Te_rel'] = False
xpoint['assume_tor_rot'] = True

xpoint.set_puretor()
runfolder = 'run'
run = Run('.', runfolder, '../../../../QuaLiKiz', qualikiz_plan=qualikiz_plan_base)
batch = Batch('.', runfolder, [run])

batch.prepare(overwrite_batch=True)
batch.generate_input()
batch.launch()
batch.to_netcdf()
os.rename(os.path.join(runfolder, runfolder + '.nc'),
          os.getcwd().split(os.path.sep)[-1] + '.nc')
