"""
Usage:
  qualikiz_tools plot [-v | -vv] [--norm <normalization>] [--flux <flux>] [--mode <mode>] [--sepH | --sumH] [--keepnH | --dropnH] <target_path>...
  qualikiz_tools plot [-v | -vv] help

Searches all sub-directories for QuaLiKiz output netCDF files (for example, generated with `qualikiztool output to_netcdf`) and plot them.

Options:
  --norm <normalization>              The normalization used (SI or GB) [default: SI]
  --flux <flux>                       The flux type to plot. These are all three-letter QuaLiKiz outputs (e.g. ef, pf, vc) [default: ef]
  --mode <mode>                       The mode to plot, (e.g. nothing/total, ETG, ITG or TEM) [default: ]
  --sepH                              Keep separate contributions of hydrogen isotopes
  --sumH                              Sum separate contributions of hydrogen isotopes together
  --keepnH                            Keep non-hydrogen isotopes
  --dropnH                            Drop non-hydrogen isotopes
  -h --help                           Show this screen.
  [-v | -vv]                          Verbosity

Examples:
    Plot ITG heat flux not summing over all hydrogen species and dropping all non-hydrogen species:
    qualikiz_tools plot --flux ef --mode ITG --sepH --dropnH.

"""
from docopt import docopt
from json import dumps
from subprocess import call
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
import xarray as xr
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch
from qualikiz_tools.plottools.plot_fluxlike import build_plot
from qualikiz_tools import __version__ as VERSION
from qualikiz_tools import __path__ as ROOT
ROOT = ROOT[0]

if __name__ == '__main__':
    print (docopt(__doc__))

def run(args):
    args = docopt(__doc__, argv=args)

    if args['-v'] >= 2:
        print ('plot received:')
        print (args)
        print ()


    #if args['--flux'] == 'ef':
    #    sum_hydrogen = True
    #else:
    #    sum_hydrogen = False

    if args['--sumH'] or args['--flux'] == 'ef':
        sum_hydrogen = True
    else:
        sum_hydrogen = False
    if args['--sepH']:
        sum_hydrogen = False

    if args['--dropnH']:
        drop_non_hydrogen = True
    else:
        drop_non_hydrogen = False
    if args['--keepnH']:
        drop_non_hydrogen = False

    path_list = args['<target_path>']
    dataset_paths = []
    if all([os.path.isdir(path) for path in path_list]):
        for root_path in path_list:
            for root, dirs, files in os.walk(root_path):
                for file in files:
                    if file.endswith('.nc'):
                        file_path = os.path.join(root, file)
                        dataset_paths.append(file_path)
                        if args['-v'] >= 1:
                            print(file_path)
        if len(dataset_paths) == 0:
            raise Exception('No datasets found')
        else:
            datasets = []
            for file_path in dataset_paths:
                ds = xr.open_dataset(file_path)
                datasets.append(ds)

            build_plot(datasets, args['--flux'], args['--norm'],
                       instability_tag=args['--mode'],
                       sum_hydrogen=sum_hydrogen,
                       drop_non_hydrogen=drop_non_hydrogen
                       )

    elif args['<target_path>'][0] in ['help', None]:
        exit(call([sys.executable, os.path.join(ROOT, 'commands', 'plot.py'), '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools plot help'." % args['<target_path>'])
