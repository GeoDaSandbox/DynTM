# Setup Django for testing outside a server environment.
if __name__=='__main__':
    import sys,os
    sys.path.append('/Users/charlie/Documents/repos/geodacenter/geodaWeb/trunk/django/Projects')
    os.environ['DJANGO_SETTINGS_MODULE']='gws_sqlite.settings'
#from google.appengine.ext import db
from gws_lib import db
from geodaWebServices import shapeManager
from struct import pack
from zlib import crc32
import zlib
import array
UNSIGNED_ITEM_TYPES = {array.array('B').itemsize:'B', array.array('H').itemsize:'H', array.array('I').itemsize:'I', array.array('L').itemsize:'L'}
from render import colors
import time
###
###        Classification <----
###        ^                  ^
###        |                  | -> ColorScheme    
###        |                  | -> ColorScheme    
###        |                  | -> ColorScheme    
###        |
###        TileSet <----------
###         ^         ^      ^
###         |         |      |
###         Tile      Tile   Tile
###
###
class Tile(db.Model):
    """Tile: This model represents a cached Tile, the core of the Dynamic mapping system
        key_name: the key_name must be set to,
            t:tileSetName:z+x+y
        typ: should be in the set(['A','B','C','D'])
        dat: the ByteString for the given tile, format of str depends on typ

    Example:
    >>> t = Tile('tile:fakedata:0+0+0')
    >>> t.typ = 'A'
    >>> t.dat = "blahblahblah"
    >>> print t.put()
    tile:fakedata:0+0+0
    >>> time.sleep(1) #sleep 1 second.
    >>> Tile.get('tile:fakedata:0+0+0').dat
    'blahblahblah'
    >>> t.delete()
    """
    typ = db.ByteStringProperty(indexed=False)
    dat = db.BlobProperty()
#class Overview(Tile):
#    """ Overview: This model represents the TileSet overview, it mimics a Tile adding a width and height.
#        key_name: the key_name must be set to,
#            o:tileSetName
#        typ: should be in the set(['A','B','C','D'])
#        dat: the ByteString for the given tile, format of str depends on typ
#        width: in pixels
#        height: in pixels
#    Example:
#    >>> o = Overview('fakedata')
#    >>> o.typ = 'A'
#    >>> o.dat = 'blahblahblah'
#    >>> o.width = 512
#    >>> o.height = 512
#    >>> print o.put()
#    fakedata
#    >>> time.sleep(1) #sleep 1 second.
#    >>> Overview.get('fakedata').dat
#    'blahblahblah'
#    >>> o.delete()
#    """
#    width = db.IntegerProperty(default=512)
#    height = db.IntegerProperty(default=512)
#class TileSet_IDS(db.Model):
#    """ TileSet_IDS: This model keeps track of the Unique IDS associated with a given TileSet.
#        key_name: the key_name must be set to,
#            tsids:tileSetName
#        ids: == zlib.compress(','.join(sorted_list_of_id_strings))
#    Example:
#    >>> import zlib
#    >>> ids = TileSet_IDS("tsids:tileSetName")
#    >>> ids.ids = zlib.compress(','.join(map(str,range(25))))
#    >>> ids.put()
#    'tsids:tileSetName'
#    >>> time.sleep(1) #sleep 1 second.
#    >>> i = TileSet_IDS.get("tsids:tileSetName")
#    >>> zlib.decompress(i.ids)
#    '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24'
#    >>> i.delete()
#    """
#    ids = db.BlobProperty()
class TileSet(db.Model):
    """ NamedTileSet: This model represents a Set of Tiles associated with a set of IDS
        key_name: the key_name must be set to:
            ts:username:md5
        notes: Anything you want
        source: information about the source data
        owner: UserProperty for the owner of the TileSet
        public: True/False
        date: Date added.
        geometry: Reference to shapeManager.models.Shapefile
        idName: name of the default Unique ID
        idLen: Number of Unique IDS
    """
    owner = db.UserProperty()
    public = db.BooleanProperty()
    date = db.DateTimeProperty()
    numregions = db.IntegerProperty()
    shpfile = db.ReferenceProperty(shapeManager.models.Shapefile)
    
#class TileSet_old(db.Model):
#    """ TileSet: This model represents a Set of Tiles.
#        key_name: the key_name must be set to:
#            ts:tileSetName
#        name: The name of the tile set
#        notes: Anything you want
#        source: information about the source data
#        owner: UserProperty for the owner of the TileSet
#        public: True/False
#        date: Date added.
#        overview: Overview property
#        idName: name of the default Unique ID
#        idLen: Number of Unique IDS
#        cLat, cLng:  Center of the TileSet in WGS84
#        minx,miny,maxx,maxy: Bounds of the TileSet in WGS84
#        maxZoom: the max zoom level for which tiles have been stored.
#    """
#    #key_name = 'ts:'+name
#    name = db.StringProperty(multiline=False) # STLCounties
#    notes = db.StringProperty(multiline=True) #blah blah blah
#    source = db.StringProperty(multiline=True) #US. Cenesus
#    owner = db.UserProperty()
#    public = db.BooleanProperty(default=True)
#    date = db.DateTimeProperty(auto_now_add=True)
#    overview = db.ReferenceProperty(Overview)
#    idName = db.StringProperty(multiline=False) #FIPS
#    idlen = db.IntegerProperty(default=0)
#    ids = db.ReferenceProperty(TileSet_IDS)
#    cLat = db.FloatProperty(default=0.0)
#    cLng = db.FloatProperty(default=0.0)
#    minx = db.FloatProperty(default=0.0)
#    miny = db.FloatProperty(default=0.0)
#    maxx = db.FloatProperty(default=0.0)
#    maxy = db.FloatProperty(default=0.0)
#    GMERC_BOUNDS = db.ListProperty(item_type=float)
#    maxZoom = db.IntegerProperty(default=0)
class Classification(db.Model):
    """ Classification: This model represents a map classification.
        key_name: the key_name must be set to:
            cl:tileSetName:classificationName
        name: Name of Classification
        tileset: Reference to the TileSet
        dat: zlib.compress(array('B').tostring()) # 'B'== UNSIGNED_INT_ONE_BYTE
            A compressed list of classes
            must begin with 0,1
        N: len(classification) - 2  == number of regions NOT including background and borders
        n: max(classification)+1 == number of colors needed to represent the classification INCLUDING background and border
        owner: UserProperty for the classification author 
        public: True/False
        expires: True/False
        date: Date added.
        title: descriptive title
        notes: details about the classification
    """
    #name = db.StringProperty(multiline=False)
    tileset = db.ReferenceProperty(TileSet)
    dat = db.BlobProperty()
    N = db.IntegerProperty(default=0)
    n = db.IntegerProperty(default=0)
    #Meta Data
    owner = db.UserProperty(auto_current_user_add=True)
    public = db.BooleanProperty(default=True)
    expires = db.BooleanProperty(default=True)
    date = db.DateTimeProperty(auto_now_add=True)
    #title = db.StringProperty()
    #notes = db.StringProperty(multiline=True) #blah blah blah
    _a = None
    @property
    def a(self):
        if self._a:
            return self._a
        else:
            arr = array.array(UNSIGNED_ITEM_TYPES[1])
            arr.fromstring(self.bytestring)
            self._a = arr
            return arr
    @property
    def bytestring(self):
        return zlib.decompress(self.dat)
    s = bytestring
    @property
    def array(self):
        return self.a

class ColorScheme(db.Model):
    """ ColorScheme: The model represents a color scheme.
        key_name: the key_name must be set to:
            cs:colorSchemeName
        name: Name of ColorScheme
        n: Number of classes INCLUDING background and borders.
            n must match the 'n' of the classification to which you apply the colorScheme.
        colors: A List of packed color values.
        alphas: A packed string of alpha values.
        #Meta
        owner: UserProperty for the colorScheme author
        public: True/False
        expires: True/False
        date: Date added.
        title: descriptive title
    """
    #name = db.StringProperty(multiline=False)
    n = db.IntegerProperty(default=0)
    colors = db.ListProperty(item_type=db.ByteString)
    alphas = db.BlobProperty(default='\x00')
    #Meta Data
    owner = db.UserProperty(auto_current_user_add=True)
    public = db.BooleanProperty(default=True)
    expires = db.BooleanProperty(default=True)
    date = db.DateTimeProperty(auto_now_add=True)
    #title = db.StringProperty()
    @property
    def PLTE(self):
        return colors.PLTE(self.colors)
    @property
    def tRNS(self):
        return colors.tRNS(self.alphas)
    def IDX(self,idx):
        return colors.ColorScheme(self.colors,self.alphas).IDX(idx)
#    def IDX(self,idx):
#        """ given the supplied class ID index list, return a new colorScheme to match
#            >>> C = fade(5)
#            >>> newC = C.IDX([0,1,4,3,3])
#        """
#        cs = colors.ColorScheme(map(self.colors.__getitem__,idx))
#        if self.alphas:
#            a = self.alphas
#            dAlpha = dict(zip(range(len(a)),a))
#            nAlpha = [dAlpha.get(id,'\xff') for id in idx]
#            while nAlpha and nAlpha[-1] == '\xff': nAlpha.pop(-1)
#            if nAlpha:
#                cs.alphas = ''.join(nAlpha)
#            else:
#                cs.alphas = colors.NO_tRNS
#        else:
#            cs.alphas = colors.NO_tRNS
#        return cs

if __name__=='__main__':
    import time
    #import doctest
    #doctest.testmod()
    #TileSet._install()
