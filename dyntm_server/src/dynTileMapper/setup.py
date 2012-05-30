#!/usr/bin/env python
from distutils.core import setup
setup(name = 'dynTileMapper',
      description = 'DynTM: Dynamic Tile Mapper',
      author = 'Charles Schmidt',
      url = 'http://geodacenter.asu.edu',
      version = '0.2',
      packages = ['dynTileMapper',
                  'dynTileMapper.pypng',
                  'dynTileMapper.tileMaker',
                  'dynTileMapper.dtm_wsgi',
                  'render'],
      #package_dir = {'dynTileMapper':'dynTileMapper'},
      #scripts = ['dynTileMapper/scripts/optTile','dynTileMapper/scripts/getTile']
     )
