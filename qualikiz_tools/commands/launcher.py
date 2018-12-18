"""
Usage:
  qualikiz_tools launcher [-v | -vv] [--stdout <path>] [--stderr <path>] <command> <machine> <target_path>
  qualikiz_tools launcher [-v | -vv] help

  Launch a job using the machine-specific QuaLiKiz tools. In principle the 'bash' machine is machine-agnostic. It needs bash and mpirun at minimum. This command will create input binaries if they are missing.

Options:
  --version <version>               Version of QuaLiKiz to generate input for [default: current]
  --stdout <path>                   Path to put STDOUT. Default depends on <machine>.
  --stderr <path>                   Path to put STDERR. Default depends on <machine>.
  -h --help                         Show this screen.
  [-v | -vv]                        Verbosity

Example command:
  qualikiz_tools launcher launch bash .

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
try:
    ModuleNotFoundError
except NameError:
    ModuleNotFoundError = ImportError

if __name__ == '__main__':
    print (docopt(__doc__))

def run(args):
    args = docopt(__doc__, argv=args)

    if args['-v'] >= 2:
        print ('output received:')
        print (args)
        print ()


    # Detect the type of path given; QuaLiKizBatch or QuaLiKizRun
    if args['<machine>'] not in ['help', None]:
        try:
            _temp = __import__('qualikiz_tools.machine_specific.' + args['<machine>'],
                               fromlist=['Run', 'Batch'])
        except ModuleNotFoundError:
            raise NotImplementedError('Machine {!s} not implemented yet'.format(args['<machine>']))
        Run, Batch = _temp.Run, _temp.Batch
        kwargs = {}
        if args['--stdout'] is not None:
            kwargs['stdout'] = args['--stdout']
        if args['--stderr'] is not None:
            kwargs['stderr'] = args['--stderr']
        if args['-v'] >= 1:
            kwargs['verbose'] = True
        __, qlk_instance = qlk_from_dir(args['<target_path>'], batch_class=Batch, run_class=Run, **kwargs)

        if args['-v'] >= 1:
            print('Supplied dir ' + args['<target_path>'] + ' is of type ' + str(qlk_instance.__class__))
    #if dirtype != 'batch':
    #    raise Exception('QuaLiKiz instance should be of type `Batch`')

    kwargs = {}
    if args['<command>'] == 'launch':
        if isinstance(qlk_instance, Run):
            qlk_instance.prepare(overwrite=False)
        elif isinstance(qlk_instance, Batch):
            qlk_instance.prepare(overwrite_batch=False, overwrite_batch_script=True)
        else:
            raise Exception('Unrecognized instance {!s} for machine {!s}'.format(qlk_instance, args['<machine>']))
        qlk_instance.generate_input()
        qlk_instance.launch()
    elif args['<target_path>'] in ['help', None] or args['<command>'] in ['help', None]:
        exit(call([sys.executable, __file__, '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools launcher help'." % args['<target_path>'])
