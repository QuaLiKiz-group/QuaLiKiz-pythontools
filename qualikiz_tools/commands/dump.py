"""
Usage: 
  qualikiz_tools dump <target_path>
  qualikiz_tools [-v | -vv] dump <target_path>

Options:
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
    
    if args['<target_path>']:
        args['<target_path>'] = os.path.abspath(args['<target_path>'])
        from qualikiz_tools.fs_manipulation.compare import bin_to_np
        print (bin_to_np(args['<target_path>']))

    elif args['<target_path>'] in ['help', None]:
        exit(call([sys.executable, os.path.join(ROOT, 'commands', 'create.py'), '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools dump help'." % args['<target_path>'])

def create_mini(target_dir):
    call([sys.executable, os.path.join(ROOT, 'examples', 'mini.py'), target_dir])

def create_performance(target_dir):
    call([sys.executable, os.path.join(ROOT, 'examples', 'performance.py'), target_dir])
