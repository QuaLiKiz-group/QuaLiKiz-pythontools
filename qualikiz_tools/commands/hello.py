"""The hello command."""


from json import dumps

def run(args):
    print ('Hello, world!')
    print ('You supplied the following options:', dumps(args, indent=2, sort_keys=True))
