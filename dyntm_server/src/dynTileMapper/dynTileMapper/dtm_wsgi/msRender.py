from gws_lib.config import MAP_FILE_HOME
import dynTileMapper.tileMaker.tiler as tiler
import yaml
from dynTileMapper.pypng import png
from dynTileMapper.pypng.optTile import optTile
from cStringIO import StringIO
import os.path
import base64,zlib

def tile_from_ms(mapName,zoom,x,y):
    """ Draw a tile on request using MapServer, store in DB.
    Example:
    >>> t = tile_from_ms('stlhom',0,0,0)
    >>> t.key_name
    't:stlhom:0+0+0'
    >>> import models
    >>> t2 = models.Tile.get_by_key_name(t.key_name)
    >>> t2.key_name == t.key_name
    True
    >>> t2.typ
    'D'
    >>> t2.dat == t.dat
    True
    """
    from dynTileMapper.dtm_wsgi.models import Tile
    tid = 't:%s:%d+%d+%d'%(mapName,zoom,x,y)
    tile = Tile(tid)
    mapfile = os.path.join(MAP_FILE_HOME,mapName,'dtm.map')
    img = StringIO(tiler.Tiler(mapfile).gTileDraw(x,y,zoom))
    typ,dat = optTile(png.PNG(img),False)
    tile.typ = typ
    tile.dat = dat
    tile.put()
    return tile

def tileSet_from_yaml(mapName):
    """ Import a TileSet and related models from a YAML file.
    Example:
    >>> ts = tileSet_from_yaml('stlhom')
    >>> ts.name
    'stlhom'
    >>> import models
    >>> t = models.TileSet.get_by_key_name('ts:stlhom')
    >>> t.name
    'stlhom'
    >>> t.overview
    'o:stlhom'
    >>> t.ids
    'tsids:stlhom'
    """
    from dynTileMapper.dtm_wsgi.models import TileSet,Overview,TileSet_IDS
    ymlfile = os.path.join(MAP_FILE_HOME,mapName,'dtm.yaml')
    m = yaml.load(open(ymlfile).read())
    overview = Overview(key_name='o:'+m.name)
    overview.typ = m.overview_typ
    overview.dat = base64.b64decode(m.overview_dat)
    overview.width = m.overview_width
    overview.height = m.overview_height
    overview_key = overview.put()
    tsids = TileSet_IDS(key_name='tsids:'+m.name)
    tsids.ids = zlib.compress(m.ids)
    tsids_key = tsids.put()
    tile_set = TileSet(key_name='ts:'+m.name)
    tile_set.public = True
    tile_set.name = m.name
    tile_set.notes = m.notes
    tile_set.source = m.source
    tile_set.idName = m.variableNames[m.idVariable]
    tile_set.idlen = len(m.ids.split(','))
    tile_set.cLng = m.cLng
    tile_set.cLat = m.cLat
    tile_set.minx = m.minx
    tile_set.miny = m.miny
    tile_set.maxx = m.maxx
    tile_set.maxy = m.maxy
    tile_set.GMERC_BOUNDS = m.gmerc_bounds
    tile_set.maxZoom = 20
    tile_set.overview = overview_key
    tile_set.ids = tsids_key
    tile_set.put()
    return tile_set


    #maptools.MapScriptObj(shpfile,size=(512,512))
    #m = mapscript.mapObj(mapfile)
    #ts.minx = m.extent.minx
    #ts.miny = m.extent.miny
    #ts.maxx = m.extent.maxx
    #ts.maxy = m.extent.maxy
#class TileSet_IDS(db.Model):
#   """ TileSet_IDS: This model keeps track of the Unique IDS associated with a given TileSet.
#   key_name: the key_name must be set to,
#   tsids:tileSetName
#   ids: == zlib.compress(','.join(sorted_list_of_id_strings))
#   """
#   ids = db.BlobProperty()
if __name__=='__main__':
    import doctest
    doctest.testmod()

