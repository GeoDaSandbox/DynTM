"""
PyPNG: Pure Python PNG Library
--------------------------------------------------------
AUTHOR: Charles Schmidt charles.r.schmidt@asu.edu
--------------------------------------------------------
Copyright (c) 2008-2009 Charles R. Schmidt
========================================================
"""
import itertools
from zlib import crc32,compress,decompressobj
from struct import pack,unpack
from StringIO import StringIO
from bitdepth import Btoii,Btoiiii,Bto8i
from base64 import b64encode
from array import array
try:
    import numpy as N
except:
    N = None

PNG_SIGNATURE = '\x89PNG\r\n\x1a\n'
PNG_RGB = 2
PNG_PLT = 3
PNG_RGBA = 6
IHDR_KEYS = ('width','height','bitdepth','colortype','compression','filter','interlace')

# Rewrite to use array
# import array
# from sys import byteorder


class Filter:
    """ Implements Filter Method 0 and all its filter Types as defined by the PNG SPEC.
        Source: http://www.w3.org/TR/PNG/#9Filters
            Byte Layout (example of where x is the blue sample):
                __c __b
                __a __x

        typical usage:
        >>> filter = Filter()
        >>> for row in filteredRaster:
        ...     row = filter(row)
        >>>
        >>> #or
        >>> newRows = maps(filter,rows)
    """
    def __init__(self,reconstruct=True,bytesPerPixel=3):
        """ reconstruct = True, means we are reconstructing image data from filter data """
        self.prev = None
        self.reconstruct = reconstruct
        self.bpp = bytesPerPixel
        #filter dispatch
        if reconstruct:
            self.dispatch = {}
            self.dispatch[1] = self.__rfilter_sub
            self.dispatch[2] = self.__rfilter_up
            self.dispatch[3] = self.__rfilter_avg
            self.dispatch[4] = self.__rfilter_paeth
        else:
            self.dispatch = {}
            self.dispatch[1] = self.__filter_sub
            self.dispatch[2] = self.__filter_up
            self.dispatch[3] = self.__filter_avg
            self.dispatch[4] = self.__filter_paeth
        self.paethCache = {}
    def __call__(self,row):
        """ each row is a row list of ints where len(row) == 1+pixels*bytesPerPixel
            the first int is the filterType
        """
        filterType = row.pop(0)
        if filterType: #i.e. not none and >0
            result = self.dispatch[filterType](row,self.prev)
            self.prev = result
            return result
        else:
            self.prev = row
            return self.prev
        
    def __rfilter_sub(self,curRow,prevRow):
        """ Filter Type: 1
            Name: Sub
            Reconstruction Function: Recon(x) = Filt(x) + Recon(a)
        """
        bytesPerPixel = self.bpp
        for i in xrange(bytesPerPixel):
            curRow.insert(0,0) #add an empty pixel to the being of the row
        #reconstruct the image data
        for i in xrange(bytesPerPixel,len(curRow)):
            curRow[i] = (curRow[i]+curRow[i-bytesPerPixel])%256 #Unsigned arithmetic modulo 256
        result = curRow
        for i in xrange(bytesPerPixel):
            assert curRow.pop(0) == 0 #remove empty pixel
        return result
    def __filter_sub(self,curRow,prevRow):
        """ Filter Type: 1
            Name: Sub
            Filter Function: Filt(x) = Orig(x) - Orig(a)
        """
        bytesPerPixel = self.bpp
        for i in xrange(bytesPerPixel):
            curRow.insert(0,0) #add an empty pixel to the being of the row
            #filter the image data
        result = [curRow[i]-curRow[i-bytesPerPixel] for i in xrange(bytesPerPixel,len(curRow))]
        for i in xrange(bytesPerPixel):
            assert curRow.pop(0) == 0 #remove empty pixel
        return result
    @staticmethod
    def __rfilter_up(curRow,prevRow):
        """ Filter Type: 2
            Name: Up
            Reconstruction Function: Recon(x) = Filt(x) + Recon(b)
        """
        if not prevRow:
            prevRow = [0 for i in curRow]
        #NOTE: prevRow should be "UNFILTERED" image data
        #return [(curRow[i]+prevRow[i])%256 for i in xrange(len(curRow))]
        return [(a+b)%256 for a,b in itertools.izip(curRow,prevRow)]
    @staticmethod
    def __filter_up(curRow,prevRow):
        """ Filter Type: 2
            Name: Up
            Filter Function: Filt(x) = Orig(x) - Orig(b)
        """
        if not prevRow:
            prevRow = [0 for i in curRow]
        result = [curRow[i]-prevRow[i] for i in xrange(len(curRow))]
        return result
    def __rfilter_avg(self,curRow,prevRow):
        """ Filter Type: 3
            Name: Average
            Reconstruction Function: Recon(x) = Filt(x) + floor((Recon(a) + Recon(b)) / 2)
        """
        bytesPerPixel = self.bpp
        for i in xrange(bytesPerPixel):
            curRow.insert(0,0) #add an empty pixel to the being of the row
        if not prevRow:
            prevRow = [0 for i in curRow]
        else:
            for i in xrange(bytesPerPixel):
                prevRow.insert(0,0) #add an empty pixel to the being of the previous row
        for i in xrange(bytesPerPixel,len(curRow)):
            a = curRow[i-bytesPerPixel]
            b = prevRow[i]
            x = curRow[i]
            curRow[i] = (x+(a+b)/2)%256 #all ints, python floors automatically
        for i in xrange(bytesPerPixel):
            assert curRow.pop(0) == 0 #remove empty pixel
        return curRow
    def __filter_avg(self,curRow,prevRow):
        """ Filter Type: 3
            Name: Average
            Filter Function: Filt(x) = Orig(x) - floor((Orig(a) + Orig(b)) / 2)
        """
        bytesPerPixel = self.bpp
        for i in xrange(bytesPerPixel):
            curRow.insert(0,0) #add an empty pixel to the being of the row
        if not prevRow:
            prevRow = [0 for i in curRow]
        else:
            for i in xrange(bytesPerPixel):
                prevRow.insert(0,0) #add an empty pixel to the being of the previous row
        for i in xrange(bytesPerPixel,len(curRow)):
            a = curRow[i-bytesPerPixel]
            b = prevRow[i]
            x = curRow[i]
            curRow[i] = x-(a+b)/2 #all ints, python floors automatically
        for i in xrange(bytesPerPixel):
            assert curRow.pop(0) == 0 #remove empty pixel
        return curRow
    def __rfilter_paeth(self,curRow,prevRow):
        """ Filter Type: 4
            Name: Paeth
            Reconstruction Function: Recon(x) = Filt(x) + PaethPredictor(Recon(a), Recon(b), Recon(c))
        """
        bytesPerPixel = self.bpp
        for i in xrange(bytesPerPixel):
            curRow.insert(0,0) #add an empty pixel to the being of the row
        if not prevRow:
            prevRow = [0 for i in xrange(len(curRow))] #create an empty row at the begining
        else:
            for i in xrange(bytesPerPixel):
                prevRow.insert(0,0) #add an empty pixel to the beinging of the previous row
        for i in xrange(bytesPerPixel,len(curRow)):
            a = curRow[i-bytesPerPixel]
            b = prevRow[i]
            c = prevRow[i-bytesPerPixel]
            x = curRow[i]
            #begin __paethPredictor
            cache = self.paethCache
            if (a,b,c) in cache:
                Pr = cache[(a,b,c)]
            else:
                p = a + b - c
                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)
                if pa <= pb and pa <= pc: Pr = a
                elif pb <= pc: Pr = b
                else: Pr = c
                cache[(a,b,c)] = Pr
            #end __paethPredictor
            curRow[i] = (x+Pr)%256
            #curRow[i] = (x+self.__paethPredictor(a,b,c))%256
        for i in xrange(bytesPerPixel):
            assert curRow.pop(0) == 0 #remove empty pixel
        return curRow
    def __filter_paeth(self,curRow,prevRow):
        """ Filter Type: 4
            Name: Paeth
            Filter Function: Filt(x) = Orig(x) - PaethPredictor(Orig(a), Orig(b), Orig(c))
        """
        bytesPerPixel = self.bpp
        for i in xrange(bytesPerPixel):
            curRow.insert(0,0) #add an empty pixel to the being of the row
        if not prevRow:
            prevRow = [0 for i in curRow] #create an empty row at the begining
        else:
            for i in xrange(bytesPerPixel):
                prevRow.insert(0,0) #add an empty pixel to the beinging of the previous row
        for i in xrange(bytesPerPixel,len(curRow)):
            a = curRow[i-bytesPerPixel]
            b = prevRow[i]
            c = prevRow[i-bytesPerPixel]
            x = curRow[i]
            #begin __paethPredictor
            cache = self.paethCache
            if (a,b,c) in cache:
                Pr = cache[(a,b,c)]
            else:
                p = a + b - c
                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)
                if pa <= pb and pa <= pc: Pr = a
                elif pb <= pc: Pr = b
                else: Pr = c
                cache[(a,b,c)] = Pr
            #end __paethPredictor
            curRow[i] = x-Pr
        for i in xrange(bytesPerPixel):
            assert curRow.pop(0) == 0 #remove empty pixel
        return curRow

class PNG:
    def __init__(self,f,mode='r'):
        if isinstance(f,basestring): #if f is a string....
            f=open(f,mode)
        self.f = f
        self.data = {'IDAT':''}
        self.idat = ''
        self.decompressor = decompressobj()
        self.chunk_order = []
        # All PNG files start with an 8 byte string,
        head = f.read(8)
        assert head == PNG_SIGNATURE
        self.dispatch = dispatch = {'IHDR':self.IHDR,
                                    'IDAT':self.IDAT,
                                    'tRNS':self.tRNS,
                                    'PLTE':self.PLTE,
                                    'IEND':self.IEND}
        for CHK_tag,CHK_data in self.chunks():
            if not CHK_tag in self.chunk_order:
                self.chunk_order.append(CHK_tag)
            if CHK_tag in dispatch:
                try:
                    dispatch[CHK_tag](data=CHK_data)
                except:
                    print "error in",CHK_tag
                    raise
            else:
                print CHK_tag
                self.data[CHK_tag] = CHK_data
    def chunks(self):
        f = self.f
        while 1:
            try:
                #the first 4 bytes are the chunk size, an unsigned Int in Network byte order
                chunkSize = unpack('!I',f.read(4))[0]
                # the next 4 bytes are an ASCII chunk description,
                chunkType = f.read(4)
                #print "Chunk Type:",chunkType," is ",chunkSize," bytes long."
                chunkData = f.read(chunkSize)
                chunkCRC = unpack('!I',f.read(4))[0]
            except:
                return
            if (crc32(chunkType+chunkData) & 0xFFFFFFFF) != chunkCRC:
                raise IOError("The %s chunk is invalid, crc32(chunkType+chunkData) does not match supplied crc."%chunkType)
            yield [chunkType,chunkData]
    def pack(self,type):
        if type in self.dispatch:
            data = self.dispatch[type](read=False)
        else:
            data = self.data[type]
        size = pack('!I', len(data))
        crc = pack('!I', crc32(type+data) & 0xFFFFFFFF)
        return size+type+data+crc
        
    def save(self,f=None):
        close = False
        if f:
            if isinstance(f,basestring): #if f is a string....
                close = True
                o = open(f,'wb')
            else:
                seek = False
                o = f
        else:
            o = StringIO()
        o.write(PNG_SIGNATURE)
        for tag in self.chunk_order:
            o.write(self.pack(tag))
        if close:
            o.close()
            return None
        if seek:
            o.seek(0)
            return o.read()
        return o
        
    def IHDR(self,data=None,read=True):
        if read:
            ihdr = unpack("!2I5B",data)
            ihdr = dict(zip(IHDR_KEYS,ihdr))
            if not ihdr['filter'] == 0:
                raise TypeError('Unsupported PNG format: only filter method 0 is supported')
            if not ihdr['compression'] == 0:
                raise TypeError('Unsupported PNG format: only compression method 0 is supported')
            if not ihdr['bitdepth'] in [1,2,4,8,16]:
                raise TypeError("Unsupported PNG format: only 1, 2, 4, 8 and 16bit images are supported")
            if not ihdr['colortype'] in [PNG_RGB, PNG_PLT, PNG_RGBA]:
                raise TypeError('Unsupported PNG format: only "Truecolour","Indexed-colour" and "TrueColour with alpha" images types are supported')
            self.data['IHDR'] = ihdr
        else:
            if 'IHDR' in self.data:
                h = self.data['IHDR']
                return pack("!2I5B", h['width'],h['height'],
                    h['bitdepth'],h['colortype'], h['compression'],h['filter'], h['interlace'])
    def IDAT(self,data=None,read=True):
        """IDAT can be split accross multiple chunks,
            but they can be decompressed as a stream"""
        if read:
            self.idat += self.decompressor.decompress(data)
        else:
            return compress(self.idat,9)
    def tRNS(self,data=None,read=True):
        if read:
            self.data['tRNS'] = data
        else:
            return self.data['tRNS']
    def PLTE(self,data=None,read=True):
        if read:
            self.data['PLTE'] = [(ord(data[i]),ord(data[i+1]),ord(data[i+2])) for i in range(0,len(data),3)]
        else:
            s = ''
            for r,g,b in self.data['PLTE']:
                s += pack('!3B',r,g,b)
            return s
    def IEND(self,data=None,read=True):
        """IEND MUST be the last chunk, so we are Done reading image.
            It is now safe to decompress IDAT. """
        if read:
            try:
                self.raster = self.getRaster()
            except:
                print "ERROR getRaster failed!"
                raise
        else:
            return ''
    def getRaster(self):
        idat = self.idat
        head = self.data['IHDR']
        depth = head['bitdepth']
        width = head['width']
        height = head['height']
        colortype = head['colortype']
        bps = depth/8.0 #bytes per sample
        if colortype == PNG_RGBA:
            bpp = 4*bps #  4 samples * bytes per sample == bytes per pixel
        elif colortype == PNG_RGB:
            bpp = 3*bps
        elif colortype == PNG_PLT:
            bpp = 1*bps
            plte = self.data['PLTE']
        #widthOfScanLine = filterByte + numPixels * bytesPerPixel
        w = int(1+width*bpp)
        if w < 2: w = 2
        i = 0
        raster = []
        empty = [0 for z in range(width*3)]
        defilter = Filter(reconstruct=True,bytesPerPixel=int(bpp))
        for y in xrange(height):
            cur = array('B')
            # byte order doesn't matter for BYTEs.
            cur.fromstring(idat[i:i+w])
            cur = cur.tolist()
            scanline = defilter(cur)
            if depth == 1:
                cur = map(Bto8i,scanline)
                cur = [byte[j] for byte in cur for j in [0,1,2,3,4,5,6,7]]
                if width < 8: cur = cur[:width]
                scanline=cur
            elif depth == 2:
                cur = map(Btoiiii,scanline)
                cur = [byte[j] for byte in cur for j in [0,1,2,3]]
                if width < 4: cur = cur[:width]
                scanline=cur
            elif depth == 4:
                cur = map(Btoii,scanline)
                cur = [byte[j] for byte in cur for j in [0,1]]
                if width < 2: cur = cur[:width]
                scanline=cur
            elif depth == 16:
                #possibly the most inefficient method possible... but 16bit is rare.
                cur = [pack('2B',scanline[j],scanline[j+1]) for j in xrange(0,len(scanline),2)]
                cur = ''.join(cur)
                cur = unpack('!%dH'%(len(cur)/2),cur)
                scanline=cur
            if colortype == PNG_RGBA:
                # IGNORE ALPHA!
                #alpha = [scanline[x] for x in range(3,len(scanline),4)]
                #l = empty[:]
                #idx = 0
                #for x in range(0,len(scanline),4):
                #    l[idx] = scanline[x]
                #    idx+=1
                #    l[idx] = scanline[x+1]
                #    idx+=1
                #    l[idx] = scanline[x+2]
                #    idx+=1
                # below is not faster... not sure why?
                #scanline = [scanline[x] for x in range(len(scanline)) if (x+1)%4]
                #
                pixels = [scanline[x:x+3] for x in range(0,len(scanline),4)]
                l = list(itertools.chain(*pixels))
                #scanline2 = [pixel[color] for pixel in pixels for color in [0,1,2]]
                scanline = l
            elif colortype == PNG_PLT:
                scanline = [plte[x] for x in scanline]
                scanline = [pixel[color] for pixel in scanline for color in [0,1,2]]
            i += w
            raster.extend(scanline)
        try:
            assert len(raster) == width*height*3
        except AssertionError:
            print raster
            raise
        return raster
    def iraster(self):
        """ returns an integer raster, i = r<<16+g<<8+b
            if entire raster is one color that color is returned in a set
            if entire raster is blank, None is returned.
        """
        r = self.raster
        n = len(r)
        slic = itertools.islice
        rast = [(a<<16)+(b<<8)+c for a,b,c in itertools.izip(slic(r,0,n,3), slic(r,1,n,3), slic(r,2,n,3))]
        s = set(rast)
        if len(s) == 1 and 0 in s:
            return None
        elif len(s) == 1:
            #Flag as singleton
            return s
        else:
            return rast
    def craster(self):
        """ same as iraster, but full rasters are compressed """
        r = self.iraster()
        if r:
            if len(r) == 1:
                return r
            head = self.data['IHDR']
            size = head['width']*head['height']
            r = pack('!%si'%size,*r)
            return compress(r)
        else:
            return None
    def b64raster(self):
        """ same as craster, but full rasters are compressed and base64 enocded"""
        r = self.craster()
        if r:
            if len(r) == 1:
                return r
            return b64encode(r)
        else:
            return None
    def setRaster(self,band=None,bands=None):
        if not N:
            raise StandardError,"Numpy is required for setRaster"
        width = self.data['IHDR']['width']
        height = self.data['IHDR']['height']

        newRast = []
        if band:
            if len(band) == width*height:
                band = N.array(band).reshape((height,width))
            for row in band:
                newRow = [0]
                for i in row:
                    newRow.extend([i,i,i])
                newRast.extend(newRow)
        elif bands:
            if len(bands[0]) == width*height:
                bands = [N.array(band).reshape((height,width)) for band in bands]
            for i in xrange(height):
                newRast.append(0)
                for j in xrange(width):
                    newRast.extend([band[i,j] for band in bands])
        else:
            raise TypeError,'rast must be the same size as the original image'
        a = array('B')
        a.fromlist(newRast)
        self.idat = a.tostring()

def main(filenames):
    a = [PNG(open(f,'rb')) for f in filenames]
    return a
    
if __name__ == "__main__":
    import sys
    import cProfile
    if len(sys.argv) > 1:
        filenames = sys.argv[1:]
    else:
        filenames = ['/Users/charlie/Documents/data/pngs/tile.png']
    print
    a = main(filenames)
    #a = a[0]
    #cProfile.run('a = main(filenames)')
    #cProfile.run('b = a[0].b64raster()')


    #from PIL import Image
    #r = a.raster
    #d = [(r[i],r[i+1],r[i+2]) for i in range(0,len(r),3)]
    #if a.data['IHDR']['bitdepth'] > 8:
    #    d = [(r[i]>>8,r[i+1]>>8,r[i+2]>>8) for i in range(0,len(r),3)]
    #img = Image.new("RGB",(a.data['IHDR']['width'],a.data['IHDR']['height']))
    #img.putdata(d)
    #img.save('test.png')
