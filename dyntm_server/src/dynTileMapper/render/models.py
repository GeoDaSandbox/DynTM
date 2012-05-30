import db
import array
import zlib
###
###        Map --->|
###        ^       |
###        |       | -> ColorScheme    
###        |       | -> ColorScheme    
###        |       | -> ColorScheme    
###        |
###        TileSet <----------
###         ^         ^      ^
###         |         |      |
###         Tile      Tile   Tile
###
###
class ColorScheme(db.Model):
    len = 0 # len, NOT including black and white
    # plte must start with background and border colors.
    PLTE = ''   # packed CRC32ed PLTE
    tRNS = ''   # packed CRC32ed tRNS
class TileSet(db.Model):
    # perhaps we should call this BaseMap?
    idName = '' #FIPS
    idlen = 0
    #ids = an ordered list of IDS
    ids = '' #zipped, packed array, [id, id, id, id, id, ...]
    cLat = 0.0
    cLng = 0.0
    maxZoom = 16 # in range(0,21)
class Tile(db.Model):
    tileSetID = "nameOfTileSet"
    typeType = 2
    dat = ''
class Map(db.Model):
    #tiles = TileSet()
    classlen = 5 #number of classes (colors)
    # colorIndex <-- compressed packed array array('B',[0,1,colorID,colorID,colorID,colorID,....])
    # region 0's color == color[colorIndex[0]]
    # must start with [0, 1], background, borders, class_id, class_id, class_id.
    colorIndex = 'x\x9cc`dB\x05\xcc\xa8\x80\x05\x15\xb0\xa2\x026\x0c\x00\x00(\x05\x01@'
    def setIndex(self,n=0):
        ci = array.array('B')
        colorIndex = [2 for i in range(n)]
        colorIndex.insert(0,1)
        colorIndex.insert(0,0)
        ci.fromlist(colorIndex)
        self.colorIndex = zlib.compress(ci.tostring())
        
