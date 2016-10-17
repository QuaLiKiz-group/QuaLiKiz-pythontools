#!/usr/bin/env python3
"""
qualikiz_tools

Usage:
  qualikiz_tools <command> [<args>...]
  qualikiz_tools [-v | -vv] <command> [<args>...]

Options:
  -h --help                         Show this screen.
  [-v | -vv]                        Verbosity 
  --version                         Show version.

Examples:
  qualikiz_tools create

Help:
  For help using this tool, please open an issue on the Github repository:
  https://github.com/rdegges/skele-cli
"""


from inspect import getmembers, isclass

from docopt import docopt
from subprocess import call

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from qualikiz_tools import __version__ as VERSION


def main():
    """Main CLI entrypoint."""
    import sys
    from qualikiz_tools import commands
    from qualikiz_tools import qualikiz_io
    from qualikiz_tools import machine_specific
    from qualikiz_tools import fs_manipulation

    args = docopt(__doc__, version=VERSION, options_first=True)
    argv = [args['<command>']] + args['<args>']

    if args['-v'] >= 1:
        passing = ['-' + 'v' * args['-v']] + argv
    else:
        passing = argv

    if args['-v'] >= 2:
        print ('qualikiz_tools received:')
        print ('global arguments:')
        print (args)
        print ('command arguments:')
        print (argv)
        print ('passing:')
        print (passing)
        print ()

    if args['<command>'] == 'create':
        from qualikiz_tools.commands import create
        #print (docopt(create.__doc__, argv=argv))
        create.run(passing)
        #Create(argv).run()
    elif args['<command>'] == 'hello':
        from qualikiz_tools.commands import hello
        hello.run(passing)
    elif args['<command>'] in ['help', None]:
        exit(call([sys.executable, sys.argv[0], '--help']))
    else:
        exit("%r is not a qualikiz_tools command. See 'qualikiz_tools help'." % args['<command>'])

if __name__ == '__main__':
    main()
