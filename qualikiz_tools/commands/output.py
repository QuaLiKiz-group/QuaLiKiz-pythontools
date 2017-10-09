"""
Usage: 
  qualikiz_tools output [-v | -vv] [--orthogonal] [--genfromtxt]  <command> <target_path>
  qualikiz_tools output [-v | -vv] help

Options:
  -h --help                         Show this screen.
  [-v | -vv]                        Verbosity 

Often used commands:
  qualikiz_tools output to_netcdf <target_path>

"""
from docopt import docopt
from json import dumps
from subprocess import call
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch, qlk_from_dir
from qualikiz_tools import __version__ as VERSION
from qualikiz_tools import __path__ as ROOT
ROOT = ROOT[0]

if __name__ == '__main__':
    print (docopt(__doc__))

def run(args):
    args = docopt(__doc__, argv=args)

    if args['-v'] >= 2:
        print ('output received:')
        print (args)
        print ()

    dirtype = None
    # Detect the type of path given; QuaLiKizBatch or QuaLiKizRun
    if args['<target_path>']:
        dirtype, qlk_instance = qlk_from_dir(args['<target_path>'])
        if args['-v'] >= 1:
            print('Supplied dir ' + args['<target_path>'] + ' is of type ' + str(dirtype))


    kwargs = {}
    if args['<command>'] == 'to_netcdf':
        if args['--genfromtxt']:
            kwargs['genfromtxt'] = True
        if args['--orthogonal']:
            kwargs['runmode'] = 'orthogonal'
            if dirtype == 'batch':
                kwargs['mode'] = 'noglue'
                kwargs['clean'] = False
        qlk_instance.to_netcdf(**kwargs)

    # Some legacy commands that might need to be re-implemented
    #elif args['<command>'] == 'squeeze':
    #    from qualikiz_tools.qualikiz_io.outputfiles import squeeze_dataset, orthogonalize_dataset, determine_sizes
    #    import xarray as xr
    #    if dirtype == 'run':
    #        sizes = determine_sizes(run.rundir)
    #        name = os.path.basename(run.rundir)
    #        netcdf_path = os.path.join(run.rundir, name + '.nc')

    #        with xr.open_dataset(netcdf_path) as ds:
    #            dsnew = ds.load()
    #        dsnew = squeeze_dataset(dsnew, sizes)
    #        dsnew.to_netcdf(netcdf_path)
    #    elif dirtype == 'batch':
    #        raise NotImplementedError()

    #elif args['<command>'] == 'to_cube':
    #    from qualikiz_tools.qualikiz_io.outputfiles import squeeze_dataset, orthogonalize_dataset, determine_sizes
    #    import xarray as xr
    #    if dirtype == 'run':
    #        sizes = determine_sizes(run.rundir)
    #        name = os.path.basename(run.rundir)
    #        netcdf_path = os.path.join(run.rundir, name + '.nc')
    #        with xr.open_dataset(netcdf_path) as ds:
    #            dsnew = ds.load()
    #        dsnew = orthogonalize_dataset(dsnew)
    #        dsnew.to_netcdf(netcdf_path)
    #    elif dirtype == 'batch':
    #        raise NotImplementedError()

    #elif args['<command>'] == 'add_dims':
    #    from qualikiz_tools.qualikiz_io.outputfiles import add_dims
    #    import xarray as xr
    #    if dirtype == 'run':
    #        name = os.path.basename(run.rundir)
    #        netcdf_path = os.path.join(run.rundir, name + '.nc')
    #        with xr.open_dataset(netcdf_path) as ds:
    #            dsnew = ds.load()
    #        dsnew = add_dims(dsnew, ['smag', 'Nex'])
    #        dsnew.to_netcdf(netcdf_path + '.newdim')
    #    elif dirtype == 'batch':
    #        raise NotImplementedError()

    elif args['<target_path>'] in ['help', None] or args['<command>'] in ['help', None]:
        exit(call([sys.executable, os.path.join(ROOT, 'commands', 'output.py'), '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools output help'." % args['<target_path>'])
