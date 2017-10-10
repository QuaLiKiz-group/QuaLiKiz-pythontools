"""
Usage:
  qualikiz_tools poll [-v | -vv]  <command> <poll_path> [<database_path>]
  qualikiz_tools poll [-v | -vv] help

Options:
  -h --help                         Show this screen.
  [-v | -vv]                        Verbosity 

Often used commands:

"""
from docopt import docopt
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
    raise NotImplementedError('Polling of statistics not available yet')
    args = docopt(__doc__, argv=args)

    if args['-v'] >= 2:
        print ('output received:')
        print (args)
        print ()

    if args['<command>'] == 'basic':
        from qualikiz_tools.machine_specific.basicpoll import create_database
        if args['<database_path>']:
            database_path = args['<database_path>']
        else:
            database_path = 'polldb.sqlite3'
        create_database(args['<poll_path>'], database_path)
    elif args['<target_path>'] in ['help', None] or args['<command>'] in ['help', None]:
        exit(call([sys.executable, os.path.join(ROOT, 'commands', 'output.py'), '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools output help'." % args['<target_path>'])
