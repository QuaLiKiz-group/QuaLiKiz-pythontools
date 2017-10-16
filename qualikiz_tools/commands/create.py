"""
Usage:
  qualikiz_tools [-v | -vv] create [--as_batch <machine>] [--in_dir <directory>] [--binary_path <path>] [--name <name>] <target> [<parameter_json>]
  qualikiz_tools [-v | -vv] create --as_batch <machine> [--in_dir <directory>] [--binary_path <path>] regression
  qualikiz_tools [-v | -vv] create --as_batch <machine> [--in_dir <directory>] [--binary_path <path>] from_json <path_to_json>

Options:
    --in_dir <directory>            Create folder in this folder [default: .]
    --name <name>                   Name to give to the main folder of the run
    --binary_path <path>            Path to the QuaLiKiz binary [default: ./QuaLiKiz]
    --as_batch <machine>            Create a batch script for the specified machine
  -h --help                         Show this screen.
  [-v | -vv]                        Verbosity

Often used commands:
  qualikiz_tools create example
  qualikiz_tools create regression
  qualikiz_tools create from_json <path_to_json>

"""
from docopt import docopt
from subprocess import call
from warnings import warn
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from qualikiz_tools import __version__ as VERSION
from qualikiz_tools import __path__ as ROOT
ROOT = ROOT[0]

if __name__ == '__main__':
    print (docopt(__doc__))

def run(args):
    args = docopt(__doc__, argv=args)

    if args['-v'] >= 2:
        print ('create received:')
        print (args)
        print ()

    parent_dir = os.path.abspath(args['--in_dir'])
    if args['-v'] >= 1:
        verbose = True
    else:
        verbose = False

    name = args['--name']
    kwargs = {}
    if args['<target>'] == 'example':
        from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun
        if name is None:
            name = 'example'
        binreldir = os.path.relpath(args['--binary_path'],
                                    start=os.path.join(parent_dir, name))
        run = QuaLiKizRun(parent_dir, name, binreldir, verbose=verbose)
        run.prepare()
    elif args['<target>'] == 'regression':
        if args['--as_batch'] is None:
            raise Exception('Must supply --as_batch for target `{!s}`'.format(args['<target>']))
        if args['--name'] is not None:
            warn('--name flag not used in target `regression`')
        try:
            _temp = __import__('qualikiz_tools.machine_specific.' + args['--as_batch'],
                               fromlist=['Run', 'Batch'])
        except ModuleNotFoundError:
            raise NotImplementedError('Machine {!s} not implemented yet'.format(args['--as_batch']))
        Run, Batch = _temp.Run, _temp.Batch

        from qualikiz_tools.qualikiz_io.inputfiles import QuaLiKizPlan
        root = os.path.join(ROOT, '../qualikiz_testcases')
        json_list = []
        runlist = []
        run_parent_dir = os.path.join(parent_dir, args['<target>'])
        listdir = sorted(os.listdir(root))
        for path in listdir:
            if path.endswith('.json'):
                json_path = os.path.join(root, path)
                plan = QuaLiKizPlan.from_json(json_path)
                name = os.path.basename(path.split('.')[0])
                binreldir = os.path.relpath(args['--binary_path'],
                                         start=os.path.join(run_parent_dir, name))
                run = Run(run_parent_dir, name, binreldir, qualikiz_plan=plan, verbose=verbose)
                runlist.append(run)
        batch = Batch(parent_dir, args['<target>'], runlist, **kwargs)
        batch.prepare()

    #if args['<target>'] == 'mini':
    #    create_mini(parent_dir)
    #elif args['<target>'] == 'performance':
    #    create_performance(parent_dir)
    elif args['<target>'] == 'from_json':
        json_path = args['<parameter_json>']
        if json_path is None:
            raise Exception("Please supply a path to a JSON file. See 'qualikiz_tools create help'")
        from qualikiz_tools.qualikiz_io.inputfiles import QuaLiKizPlan
        plan = QuaLiKizPlan.from_json(json_path)

        from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch
        if name is None:
            name = os.path.basename(json_path.split('.')[0])
        binreldir = os.path.relpath(args['--binary_path'],
                                         start=os.path.join(parent_dir, name))
        if args['--as_batch'] is None:
            run = QuaLiKizRun(parent_dir, name, binreldir, qualikiz_plan=plan, verbose=verbose)
            run.prepare()
        else:
            try:
                _temp = __import__('qualikiz_tools.machine_specific.' + args['--as_batch'],
                                   fromlist=['Run', 'Batch'])
            except ModuleNotFoundError:
                raise NotImplementedError('Machine {!s} not implemented yet'.format(args['--as_batch']))
            Run, Batch = _temp.Run, _temp.Batch
            run = Run(parent_dir, name, binreldir, qualikiz_plan=plan, verbose=verbose)
            batch = Batch(parent_dir, name, [run], **kwargs)
            batch.prepare()
    elif args['<target>'] in ['help', None]:
        exit(call([sys.executable, os.path.join(ROOT, 'commands', 'create.py'), '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools create help'." % args['<target>'])

#def create_mini(target_dir):
#    call([sys.executable, os.path.join(ROOT, 'examples', 'mini.py'), target_dir])

def create_performance(target_dir):
    call([sys.executable, os.path.join(ROOT, 'examples', 'performance.py'), target_dir])
