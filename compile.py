#!/usr/bin/env python

""" Description..."""

__author__ = "Peter Bennett"
__copyright__ = "Copyright 2012, Peter A Bennett"
__license__ = "LGPL"
__version__ = "0.1"
__maintainer__ = "Peter Bennett"
__email__ = "pab850@googlemail.com"
__contact__ = "www.bytebash.com"

from distutils.core import setup
import py2exe
 
setup(
    windows = ['qt_schematix.py'],
    options = {
        "py2exe" : {
            "includes" : ['sys', 'tempfile', 'zipfile', 'mmap', 'encodings',
                          'json', 'hashlib', 'datetime', 'struct',
                          'os', 'time', 'random', 'math', 'xmlrpclib'],
            "compressed" : 1,
            "optimize" : 2,
            "ascii" : 1,
            "bundle_files": 1
        }
    }
)