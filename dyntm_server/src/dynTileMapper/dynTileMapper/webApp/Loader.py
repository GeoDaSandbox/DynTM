import base64
from google.appengine.ext import db
from google.appengine.tools import bulkloader
class TileLoader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Tile', [('typ',db.ByteString),('dat',self.debase)])
    def initialize(self,filename,loader_opts):
        if loader_opts:
            print loader_opts
            self.TILE_SET_ID = loader_opts
        bulkloader.Loader.initialize(self,filename,loader_opts)
    def debase(self,v):
        if v.isdigit():
            return v
        else:
            try: 
                return base64.b64decode(v)
            except:
                return v
    def generate_key(self, i, values):
        z = values.pop(0)
        x = values.pop(0)
        y = values.pop(0)
        return "t:%s:%s+%s+%s"%(self.TILE_SET_ID,z,x,y)
loaders = [TileLoader]


LOADER_FILE = """import base64
from google.appengine.ext import db
from google.appengine.tools import bulkloader
class TileLoader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Tile', [('typ',db.ByteString),('dat',self.debase)])
    def initialize(self,filename,loader_opts):
        if loader_opts:
            print loader_opts
            self.TILE_SET_ID = loader_opts
        bulkloader.Loader.initialize(self,filename,loader_opts)
    def debase(self,v):
        if v.isdigit():
            return v
        else:
            try: 
                return base64.b64decode(v)
            except:
                return v
    def generate_key(self, i, values):
        z = values.pop(0)
        x = values.pop(0)
        y = values.pop(0)
        return "t:%s:%s+%s+%s"%(self.TILE_SET_ID,z,x,y)
loaders = [TileLoader]
"""
