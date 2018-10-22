"""
Usage:
  qualikiz_tools input [-v | -vv] [--version <version>] <command> <target_path>
  qualikiz_tools input [-v | -vv] help

  For example, create input binaries for QuaLiKiz batch or run contained in <target_path>
      qualikiz_tools input generate <target_path>

Options:
  --version <version>               Version of QuaLiKiz to generate input for [default: current]
  -h --help                         Show this screen.
  [-v | -vv]                        Verbosity 

Often used commands:
  qualikiz_tools input generate <target_path>

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
    if args['<target_path>']:
        dirtype, qlk_instance = qlk_from_dir(args['<target_path>'])
        if args['-v'] >= 1:
            print('Supplied dir ' + args['<target_path>'] + ' is of type ' + str(qlk_instance.__class__))
        kwargs = {}
        if args['<command>'] == 'generate':
            if args['-v'] >= 2:
                kwargs['dotprint'] = True
            if args['--version'] == 'current':
                pass
            elif args['--version'] in ['2.4.0', '2.3.2', '2.3.1', 'CEA_QuaLiKiz']:
                from qualikiz_tools.qualikiz_io.legacy import convert_current_to
                convert = lambda inputdir: convert_current_to(inputdir, target=args['--version'])
                kwargs['conversion'] = convert
            else:
                raise Exception('Unknown version {!s}'.format(args['--version']))
            qlk_instance.generate_input(**kwargs)

    elif args['<target_path>'] in ['help', None] or args['<command>'] in ['help', None]:
        exit(call([sys.executable, __file__, '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools input help'." % args['<target_path>'])
