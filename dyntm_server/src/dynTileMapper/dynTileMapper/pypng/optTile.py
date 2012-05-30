"""
-----------------
Filename: optTile.py
Use: Optimzes Tiles for storing in Google App Engine
Needs: png.py

Takes an instance of PNG, and determines thebest format to store the raster.
Outputs are: singleton, plte, full raster.

Usage:
>>> tileType,strTile = optTile(png)
"""
import zlib
from base64 import b64encode,b64decode
from sys import byteorder
if byteorder == 'little':
    SYSTEM_BYTEORDER = '\x00'
elif byteorder == 'big':
    SYSTEM_BYTEORDER = '\x01'
else:
    raise TypeError,"Unknown endian: %s"%byteorder
from array import array
UNSIGNED_ITEM_TYPES = {array('B').itemsize:'B', array('H').itemsize:'H', array('I').itemsize:'I', array('L').itemsize:'L'}
from struct import pack,unpack
from zlib import crc32

BLANKTILE = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x03\x00\x00\x00%\xdbV\xca\x00\x00\x00\x03PLTE\xff\xff\xff\xa7\xc4\x1b\xc8\x00\x00\x00\x01tRNS\x00@\xe6\xd8f\x00\x00\x00\x12IDATx^\x05\xc0\x81\x08\x00\x00\x00\x00\xa0\xfd\xa9\x8f\x00\x02\x00\x01t;RG\x00\x00\x00\x00IEND\xaeB`\x82'

BLANK_ID = 'A'
SINGLETON_ID = 'B'
INTERGER_RASTER_ID = 'C'
PLTE_ID = 'D'


class Singleton: #a sole region
    def __init__(self,regionId):
        assert len(regionId) == 1
        self.regionId = regionId.pop()
    def __call__(self):
        return self.regionId
class IntegerRaster:
    """ Pack an intRaster with 2 byte header into a base64 string
        byte 0: (byteOrder) \x00==little, \x01==big
        byte 1: (dtype) \x00=='?' unsigned 2byte int, \x01 == '?' unsigned 4byte int
    """
    def __init__(self,intRaster,maxID):
        self.intRaster = intRaster
        self.maxID = maxID
    def __call__(self,encode=True):
        if self.maxID < 2**16:
            dtype = UNSIGNED_ITEM_TYPES[2] #UNSIGNED_2_BYTE_INT
            DTYPE = '\x00'
        else:
            dtype = UNSIGNED_ITEM_TYPES[4] #UNSIGNED_4_BYTE_INT
            DTYPE = '\x01'
        a = array(dtype)
        a.fromlist(self.intRaster)
        if encode:
            return b64encode(SYSTEM_BYTEORDER+DTYPE+zlib.compress(a.tostring()))
        else:
            return SYSTEM_BYTEORDER+DTYPE+zlib.compress(a.tostring())
    def verify(self,s):
        s = b64decode(s)
        byteorder = s[0]
        dtype = s[1]
        if dtype == '\x00': dtype = UNSIGNED_ITEM_TYPES[2]
        else: dtype = UNSIGNED_ITEM_TYPES[4]
        a = array(dtype)
        a.fromstring(zlib.decompress(s[2:]))
        if byteorder != SYSTEM_BYTEORDER:
            a.byteswap()
        assert a.tolist() == self.intRaster
        
class PLTE: # an indexed palette
    """ Palletizes an intRaster and packs it into a base64 encoded string.
        9 byte header:
        byte0 = ByteOrder
        byte1:4 = in "!" network byte order len of IDAT
        byte4:8 = in "!" network byte order len of PLTE
        byte9:n = ready to go IDAT (in network (big) byteorder)
        byten:  = cPLTE
    
        Raises IOError is raster has too many regions (>256)
    """
    def __init__(self,intRaster,regions=None,n=None,width=None):
        if regions and n:
            plte = list(regions)
        else:
            plte = list(set(intRaster))
            n = len(plte)
        if n > 255:
            raise IOError, "Too large for PLTE coloring, try using Raster format"
        plte.sort()
        self.plte = plte
        dPlte = dict(zip(plte,range(n)))
        idRaster = map(dPlte.get,intRaster)
        rows = len(idRaster)/width
        delta = width+1
        c = 0
        for i in xrange(rows):
            idRaster.insert(c,0) #add filter codes
            c+=delta
        #assert [PLTE[id] for id in idRaster] == intRaster
        self.idRaster = idRaster
        self.width = width
    def __call__(self,encode=True):
        plte = self.plte
        idRaster = self.idRaster
        a = array('B') #unsigned 1byte int
        a.fromlist(idRaster)
        if SYSTEM_BYTEORDER == '\x00': #little
            a.byteswap() #to big (network)
        cIdRaster = zlib.compress(a.tostring())
        size = pack('!I',len(cIdRaster))
        crc = pack('!I',crc32('IDAT'+cIdRaster) & 0xFFFFFFFF)
        idat = size+'IDAT'+cIdRaster+crc

        b = array(UNSIGNED_ITEM_TYPES[4]) #unsigned 4byte int
        b.fromlist(plte)
        cPLTE = zlib.compress(b.tostring())

        s = SYSTEM_BYTEORDER + pack('!LL',len(idat),len(cPLTE)) # 9bytes <--- ByteOrder(1byte), len of idat(4bytes), len of cPLTE(4bytes)
        s = s+idat+cPLTE
        if encode:
            return b64encode(s)
        else:
            return s
    def verify(self,s):
        s = b64decode(s)
        byteorder = s[0]
        lenRaster,lenPLTE = unpack('!LL',s[1:9])
        cIdRaster = s[9:9+lenRaster]
        cPLTE = s[9+lenRaster:]

        idRaster = zlib.decompress(cIdRaster)
        a = array('B')
        a.fromstring(idRaster)

        plte = zlib.decompress(cPLTE)
        b = array(UNSIGNED_ITEM_TYPES[4])
        b.fromstring(plte)
        if byteorder != SYSTEM_BYTEORDER:
            b.byteswap()
        try:
            assert self.idRaster == a.tolist()
            assert self.plte == b.tolist()
        except AssertionError:
            return a.tolist(),b.tolist()

def optTile(png,encode=True):
        intRaster = png.iraster()
        if intRaster: #not blank
            if len(intRaster) > 1: #not singleton
                regions = set(intRaster) #unique integeres (colors/regions) in the raster
                n = len(regions)
                if n < 256:
                    return PLTE_ID,PLTE(intRaster,regions,n,width=png.data['IHDR']['width'])(encode)
                else:
                    return INTERGER_RASTER_ID,IntegerRaster(intRaster,max(intRaster))(encode)
            else: #singleton
                return SINGLETON_ID,Singleton(intRaster)()
        else: #blank
            if encode:
                return BLANK_ID,b64encode('\x00')
            else:
                return BLANK_ID,'\x00'

if __name__=='__main__':
    import png,sys
    if len(sys.argv) != 2:
        print "Usage: python optTile input.png"
    else:
        typ,dat = optTile(png.PNG(sys.argv[1]))
        print typ,dat
