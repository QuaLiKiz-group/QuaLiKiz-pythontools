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
  qualikiz_tools dump
  qualikiz_tools output
  qualikiz_tools poll

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
        create.run(passing)
    elif args['<command>'] == 'dump':
        from qualikiz_tools.commands import dump
        dump.run(passing)
    elif args['<command>'] == 'input':
        from qualikiz_tools.commands import input
        input.run(passing)
    elif args['<command>'] == 'launcher':
        from qualikiz_tools.commands import launcher
        launcher.run(passing)
    elif args['<command>'] == 'output':
        from qualikiz_tools.commands import output
        output.run(passing)
    elif args['<command>'] == 'plot':
        from qualikiz_tools.commands import plot
        plot.run(passing)
    elif args['<command>'] == 'poll':
        from qualikiz_tools.commands import poll
        poll.run(passing)
    elif args['<command>'] == 'hello':
        from qualikiz_tools.commands import hello
        hello.run(passing)
    elif args['<command>'] in ['help', None]:
        exit(call([sys.executable, sys.argv[0], '--help']))
    else:
        exit("%r is not a qualikiz_tools command. See 'qualikiz_tools help'." % args['<command>'])

if __name__ == '__main__':
    main()
