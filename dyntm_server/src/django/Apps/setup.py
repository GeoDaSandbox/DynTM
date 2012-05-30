"""
setup.py for GeoDaWebServices
"""

from distutils.core import setup, Extension
import os
rev = os.popen('svnversion -n').read()

setup(name = 'gws',
      description = 'gws: GeoDa Web Services',
      author = 'Charles Schmidt',
      author_email = 'Charles.R.Schmidt@asu.edu',
      url = 'http://geodacenter.asu.edu/',
      version = "0.0.6",
      packages = ['geodaWebServices', 
                  'geodaWebServices.geodaWebServiceAuth',
                  'geodaWebServices.calc',
                  'geodaWebServices.shapeManager',
                  'geodaWebServices.dyntm',
                  'geodaWebServices.classification',
                  'geodaWebServices.dict'],
     )
