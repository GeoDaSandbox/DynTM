"""
setup.py for GeoDaWebServices
"""

from distutils.core import setup, Extension
import os
rev = os.popen('svnversion -n').read()

setup(name = 'gws_lib',
      description = 'gws_lib: GeoDa Web Services Backend Libraries',
      author = 'Charles Schmidt',
      author_email = 'Charles.R.Schmidt@asu.edu',
      url = 'http://geodacenter.asu.edu/',
      version = "0.0.2",
      packages = ['gws_lib', 
                  'gws_lib.sdb'],
     )
