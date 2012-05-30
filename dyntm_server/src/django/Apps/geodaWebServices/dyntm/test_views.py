from views import TileHandler
from random import randint
from models import Tile
from render import render,classification,colors,query

class TestHandler(TileHandler):
    def __init__(self,format='png',auth=False):
        TileHandler.__init__(self,format,auth)
    @property
    def tile(self):
        z = 11
        x = randint(496,523)
        y = randint(772,797)
        try:
            z,x,y = map(int,[z,x,y])
            tid = "t:%s:%d+%d+%d"%(self.ts.shpfile,z,x,y)
            tile = Tile.get_by_key_name(tid)
            if tile:
                self._tile = tile
                return tile
            else:
                shpfile = memcache.get(self.ts.shpfile.encode('utf8'))
                if not shpfile:
                    shpfile = Shapefile.get_by_key_name(self.ts.shpfile)
                    memcache.set(self.ts.shpfile.encode('utf8'),shpfile)
                typ,dat = shpfile.raw_tile(x,y,z)
                tile = Tile(tid)
                tile.typ = typ 
                tile.dat = str(dat)
                tile.put()
                self._tile = tile
                return tile
        except:
            raise
            return False
        return False
    def get(self):
        self.tsid = 'charlie:B9C118EB30A9EAE19C93902E9F01EF8A'
        self.clid = 'charlie:474f117491ba503bde2b1eb2b9a36b3a'
        ts = self.ts
        tile = self.tile
        cl = self.cl
        if ts and tile:
            #if cl:
            #    #png = render.overview(ts.n,tile.typ,tile.dat,C=classification.Classification(cl.a))
            #    png = render.overview(ts.numregions,tile.typ,tile.dat,C=cl)
            #else:
            png = render.overview(ts.numregions,tile.typ,tile.dat,C=self.cl,CS=self.cs)
            return self.write(png)
        else:
            return self.error(404)
        return self.write("Got Here")

