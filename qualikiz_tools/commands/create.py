"""
Usage: 
  qualikiz_tools [-v | -vv] create [--in_dir <directory>] [--binary_dir <directory>] <target> [<parameter_json>]

Options:
    --in_dir <directory>              Create folder in this folder [default: runs]
    --binary_dir <directory>          Path to the QuaLiKiz binary [default: ./QuaLiKiz]
  -h --help                         Show this screen.
  [-v | -vv]                        Verbosity

Often used commands:
  qualikiz_tools create mini
  qualikiz_tools create performance

"""
from docopt import docopt
from json import dumps
from subprocess import call
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
    if args['<target>'] == 'mini':
        create_mini(parent_dir)
    elif args['<target>'] == 'performance':
        create_performance(parent_dir)
    elif args['<target>'] == 'from_json':
        json_path = args['<parameter_json>']
        if json_path is None:
            raise Exception("Please supply a path to a JSON file. See 'qualikiz_tools create help'")
        if os.path.isfile(json_path):
            from qualikiz_tools.qualikiz_io.inputfiles import QuaLiKizPlan
            plan = QuaLiKizPlan.from_json(json_path)
        else:
            raise Exception('`{!s}` is not a valid JSON file'.format(json_path))

        from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun
        name = os.path.basename(json_path.split('.')[0])
        reldir = os.path.relpath(args['--binary_dir'],
                                 start=os.path.join(parent_dir, name))
        if args['-v'] >= 1:
            verbose = True
        else:
            verbose = False
        run = QuaLiKizRun(parent_dir, name, reldir, qualikiz_plan=plan, verbose=verbose)
        run.prepare()
    elif args['<target>'] in ['help', None]:
        exit(call([sys.executable, os.path.join(ROOT, 'commands', 'create.py'), '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools create help'." % args['<target>'])

def create_mini(target_dir):
    call([sys.executable, os.path.join(ROOT, 'examples', 'mini.py'), target_dir])

def create_performance(target_dir):
    call([sys.executable, os.path.join(ROOT, 'examples', 'performance.py'), target_dir])
