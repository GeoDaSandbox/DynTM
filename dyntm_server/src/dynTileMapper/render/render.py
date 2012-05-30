import classification
import array
UNSIGNED_ITEM_TYPES = {array.array('B').itemsize:'B', array.array('H').itemsize:'H', array.array('I').itemsize:'I', array.array('L').itemsize:'L'}
import zlib
from colors import fade
from struct import unpack,pack
from sys import byteorder
import base64
if byteorder == 'little':
    SYSTEM_BYTEORDER = ord('\x00')
elif byteorder == 'big':
    SYSTEM_BYTEORDER = ord('\x01')
else:
    raise TypeError, 'Unknown endian: %s'%byteorder
PNG_SIGNATURE = '\x89PNG\r\n\x1a\n'
PLTE_HEAD = '\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x03\x00\x00\x00k\xacXT'
IEND = '\x00\x00\x00\x00IEND\xaeB`\x82'
BLANK = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
SINGLEHEAD ='\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x01\x03\x00\x00\x00f\xbc:%'
SINGLETAIL ='\x00\x00\x00\x1fIDATx^\xed\xc0\x01\t\x00\x00\x00\xc20\xfb\xa76\xc7a[\x1c\x00\x00\x00\x00\x00\x00\x00\xc0\x01!\x00\x00\x01\x83e\x0f\xe4\x00\x00\x00\x00IEND\xaeB`\x82'

#import logging

def chunk(type='IDAT',data=None):
    """ packs a PNG chunk """
    size = pack('!I',len(data))
    crc = pack('!I',zlib.crc32(type+data) & 0xFFFFFFFF)
    return size+type+data+crc
def ihdr(width,height,colorType=3):
    return chunk(type='IHDR',data=pack("!2I5B",width,height,8,colorType,0,0,0))
def render_blank(*args):
    return BLANK
def render_single(classMap,colorScheme,id,width=None,height=None):
    #logging.info('here')
    classID = classMap.a[id]
    #logging.info(classID)
    cs = colorScheme.IDX([classID])
    #logging.info(cs.colors)
    PLTE = cs.PLTE
    tRNS = cs.tRNS
    #return SINGLEHEAD+PLTE+SINGLETAIL
    return SINGLEHEAD+PLTE+tRNS+SINGLETAIL
    
def render_raster(classMap,colorScheme,tile,width=256,height=256):
    """ This function renders a Interger Raster into a PLTE based PNG.
        The assumption here is there you classification contains less than 254 clasess
    """
    byteorder = ord(tile[0])
    dtype = tile[1]
    if dtype == '\x00': dtype = UNSIGNED_ITEM_TYPES[2]
    else: dtype = UNSIGNED_ITEM_TYPES[4]
    a = array.array(dtype)
    a.fromstring(zlib.decompress(tile[2:]))
    if byteorder != SYSTEM_BYTEORDER:
        a.byteswap()
    
    s = ''
    for row in xrange(height):
        start = row*width
        r = map(classMap.s.__getitem__,a[start:start+width])
        s += '\x00'+''.join(r)
    if height == width == 256:
        plte_ihdr = PLTE_HEAD
    else:
        plte_ihdr = ihdr(width,height)
    raster = zlib.compress(s)
    return PNG_SIGNATURE+plte_ihdr+colorScheme.PLTE+colorScheme.tRNS+chunk(data=raster)+IEND
        
def render_plte(classMap,colorScheme,tile,width=256,height=256):
    dat = tile
    lenRaster, lenPLTE = unpack('!LL',dat[1:9])

    b = array.array(UNSIGNED_ITEM_TYPES[4])
    b.fromstring(zlib.decompress(dat[9+lenRaster:]))
    if ord(dat[0]) != SYSTEM_BYTEORDER:
        b.byteswap()
    classIDs = [classMap.a[i] for i in b]
    colorScheme = colorScheme.IDX(classIDs)

    PLTE = colorScheme.PLTE
    tRNS = colorScheme.tRNS

    if height == width == 256:
        plte_ihdr = PLTE_HEAD
    else:
        plte_ihdr = ihdr(width,height)
    
    if 0 in classIDs: #background in img
        return PNG_SIGNATURE+plte_ihdr+PLTE+tRNS+dat[9:9+lenRaster]+IEND
    else:
        return PNG_SIGNATURE+plte_ihdr+PLTE+dat[9:9+lenRaster]+IEND

TILE_TYPE_DISPATCH = {
            'A':render_blank, 0:render_blank, 
            'B':render_single, 1:render_single,
            'C':render_raster, 2:render_raster,
            'D':render_plte, 3:render_plte }

def overview(N,typ,dat,width=256,height=256,color=(255,90,0),C=None,CS=None):
    if not C: C = classification.random(N,3)
    #if not CS: CS = fade(steps=1,left=color,right=color,borders=(0,0,0))
    if not CS: CS = fade(steps=C.n,borders=(0,0,0))
    #if typ in 'CD':
    #    dat = base64.b64decode(dat)
    if typ == 'B':
        dat = int(dat)
    return TILE_TYPE_DISPATCH[typ](C,CS,dat,width,height)
def cache_file_to_PNGs(tileData='/Users/charlie/Documents/data/usa/usa_cache.csv',N=3111):
    """ This function is designed to help Demo and Profile the rendering code,
        It processes a txt file containing the output of the DynTileMapper GUI
        Each line the in txt file is turned into a PNG image with a random classification
    """
    C = classification.random(N,200)
    CS = fade(steps=198,left=(255,255,0),right=(0,255,255),borders=(255,0,0))
    f = open(tileData,'r')
    header = f.next() #header
    for line in f:
        z,x,y,tileType,tile = line.strip().split(',')
        fname = '%s+%s+%s.png'%(z,x,y)
        if tileType in 'CD':
            tile = base64.b64decode(tile)
        elif tileType == 'B':
            tile = int(tile)
        s = TILE_TYPE_DISPATCH[tileType](C,CS,tile)
        o = open('out/'+fname,'wb')
        o.write(s)
        o.close()
if __name__=='__main__':
#    pass
    cache_file_to_PNGs()
