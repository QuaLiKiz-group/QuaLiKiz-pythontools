QuaLiKiz-pythontools
=========

*A collection of tools for QuaLiKiz in Python.*

Purpose
-------

This is a collection of Python modules to be used for working with QuaLiKiz,
a quasi-linear gyrokinetic code. QuaLiKiz can be found on GitHub

Usage
-----

If you've cloned this project, and want to install the library (*and all
development dependencies*), the command you'll want to run is::

    $ pip install -e .[test]

If you'd like to run all tests for this project, you would run the following command::

    $ python setup.py test
    
Note that installing the library is not necessary per se, you can also use the command
line tools by just running::

    $ qualikiz_tools/cli.py
    
Or you can write your own scripts that make use of the supplied python modules. See
the folder qualikiz_tools/examples for examples.
