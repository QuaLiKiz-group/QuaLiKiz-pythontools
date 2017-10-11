"""
Usage:
  qualikiz_tools launcher [-v | -vv] <command> <machine> <target_path>
  qualikiz_tools launcher [-v | -vv] help

  For example, create input binaries for QuaLiKiz batch or run contained in <target_path>
      qualikiz_tools input create <target_path>

Options:
  --version <version>               Version of QuaLiKiz to generate input for [default: current]
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


    # Detect the type of path given; QuaLiKizBatch or QuaLiKizRun
    try:
        _temp = __import__('qualikiz_tools.machine_specific.' + args['<machine>'],
                           fromlist=['Run', 'Batch'])
    except ModuleNotFoundError:
        raise NotImplementedError('Machine {!s} not implemented yet'.format(args['<machine>']))
    Run, Batch = _temp.Run, _temp.Batch
    try:
        qlk_instance = Batch.from_dir(args['<target_path>'])
    except:
        qlk_instance = Run.from_dir(args['<target_path>'])

    if args['-v'] >= 1:
        print('Supplied dir ' + args['<target_path>'] + ' is of type ' + str(qlk_instance.__class__))
    #if dirtype != 'batch':
    #    raise Exception('QuaLiKiz instance should be of type `Batch`')

    kwargs = {}
    if args['<command>'] == 'launch':
        qlk_instance.launch()
    elif args['<target_path>'] in ['help', None] or args['<command>'] in ['help', None]:
        exit(call([sys.executable, os.path.join(ROOT, 'commands', 'output.py'), '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools output help'." % args['<target_path>'])
