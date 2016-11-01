"""
Usage: 
  qualikiz_tools [-v | -vv] output <command> <target_path>
  qualikiz_tools [-v | -vv] output help

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
from qualikiz_tools import __version__ as VERSION
from qualikiz_tools import __path__ as ROOT
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizBatch, QuaLiKizRun
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
    if args['<target_path>']:
        if os.path.exists(os.path.join(args['<target_path>'], QuaLiKizRun.parameterspath)):
            dirtype = 'run'
        elif os.path.exists(os.path.join(args['<target_path>'], QuaLiKizBatch.scriptname)):
            dirtype = 'batch'

        if args['-v'] >= 1:
            print('Supplied dir ' + args['<target_path>'] + ' is of type ' + dirtype)


    if args['<command>'] == 'to_netcdf':
        if dirtype == 'run':
            binaryname = None
            pos_binname = ['QuaLiKiz','QuaLiKiz+pat']
            for file in  os.listdir(args['<target_path>']):
                if file in pos_binname:
                    binaryname = file
                    break

            run = QuaLiKizRun.from_dir(args['<target_path>'], binaryname)
            run.to_netcdf()
        elif dirtype == 'batch':
            raise NotImplementedError()

    elif args['<target_path>'] in ['help', None] or args['<command>'] in ['help', None]:
        exit(call([sys.executable, os.path.join(ROOT, 'commands', 'output.py'), '--help']))
    else:
        exit("%r is not a valid target. See 'qualikiz_tools output help'." % args['<target_path>'])
