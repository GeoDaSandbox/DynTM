#!/usr/bin/env python
"""
colors.py: Utilities for reading and creating ColorSchemes

ColorSchemes define colors for a set of n classes.
    - n is limited to 256 classes
    - The color scheme is represented as a list ('colors') of 3byte colors.
      colors[0] is the color for the Background class and is generally (0,0,1)
      colors[1] is the color for the Borders class and is generally black (0,0,0)
      colors[i] is the color for the i'th class.
    - tRNS: ColorSchemes also define the Alpha values associated with each color.
        Each color in the color scheme is assign a value between 0 and 255.
        The default is 255 which means fully opaque.
        The background is generally given a value of 0, fully transparent.
        Any color not listed in the tRNS array is assumed to be fully opaque.
        This is why the background is first, since it is generally the only class
        we care to make transparent, we save space by have only one element in the array.
        We also save CPU time since we can cache and reuse the same tRNS chunk in each image.

        This can be manipulated for interesting effects, e.g.
            Assign all classes the color #000001 except one.
            Set the transparency on #000001 to 153 (~60%).
            The result will be that the single class not coded #000001 will standout,
            the other classes will be masked in grey.
            Problems arise from BLANK tiles which are by default fully transparent.
    
        tRNS is a string of bytes (alpha values) one for each color in the palette
        It needs to be packed into a PNG chunk.
        if no tRNS is provied the default is used.
        assert tRNS == None OR len(tRNS) == n
    
    - PLTE: PLTE refers the packed representation of the color scheme.
        It is a list of bytes, each 3 bytes represents one color.
        The 1st 3 bytes are the Red, Green and Blue values for the 1st class (background)
        The 2nd 3 bytes are the Red, Green and Blue values for the 2nd class (borders)
        The i'th 3 bytes are the Red, Green and Blue values for the i'th class...
        It needs to be packed into a PNG chunk

"""
from struct import pack
from array import array
UNSIGNED_ITEM_TYPES = {array('B').itemsize:'B', array('H').itemsize:'H', array('I').itemsize:'I', array('L').itemsize:'L'}
from zlib import crc32
from random import choice

NO_tRNS = 'no_trns'
WEB_SAFE_COLORS = [17, 34, 51, 68, 85, 102, 119, 136, 153, 170, 187, 204, 221, 238, 255]
class ColorScheme(object):
    def __init__(self, colors, alphas = [0]):
        if type(colors[0]) == tuple:
            colors = [pack('!3B',r&0xFF,g&0xFF,b&0xFF) for r,g,b in colors]
        self.__colors = colors
        self.__alphas = None
        if alphas:
            self._set_alphas(alphas)
    def _get_alphas(self):
        return self.__alphas
    def _set_alphas(self,value):
        if value == NO_tRNS:
            self.__alphas = NO_tRNS
            return
        #assert len(value) == len(self.__colors)
        if issubclass(type(value),basestring):
            self.__alphas = value
        elif value:
            trns = array(UNSIGNED_ITEM_TYPES[1])
            try:
                trns.fromlist(value)
            except OverflowError:
                raise OverflowError, "Alpha value is greater than the maximum (255)"
            self.__alphas = trns.tostring()
    alphas = property(fget=_get_alphas,fset=_set_alphas)
    @property
    def colors(self):
        return self.__colors
    @property
    def PLTE(self):
        return PLTE(self.colors)
    @property
    def tRNS(self):
        return tRNS(self.alphas)
    @property
    def n(self):
        return len(self.colors)
    def IDX(self,idx):
        """ given the supplied class ID index list, return a new colorScheme to match
            >>> C = fade(5)
            >>> newC = C.IDX([0,1,4,3,3])
        """
        cs = ColorScheme(map(self.colors.__getitem__,idx))
        if self.alphas:
            a = self.alphas
            dAlpha = dict(zip(range(len(a)),a))
            nAlpha = [dAlpha.get(id,'\xff') for id in idx]
            while nAlpha and nAlpha[-1] == '\xff': nAlpha.pop(-1)
            if nAlpha:
                cs.alphas = ''.join(nAlpha)
            else:
                cs.alphas = NO_tRNS
        else:
            cs.alphas = NO_tRNS
        return cs

class PseudoColorScheme:
    def __init__(self, n=1, left=(60,60,60), right=(200,200,200), background=(0,0,1), borders=(0,0,0)):
        """Generate a color scheme with n classes,
            fading from left to right """
        self.colors = [background,borders]+fade(n,left,right)
        self.PLTE = PLTE(self.colors)
        self.tRNS = '\x00\x00\x00\x01tRNS\x00@\xe6\xd8f' #background = 0
        self.n = len(self.colors)
    def pack(self):
        s = ''
        for r,g,b in self.colors:
            s += pack('!3B',r&0xFF,g&0xFF,b&0xFF)
        size = pack('!I', len(s))
        crc = pack('!I', crc32('PLTE'+s) & 0xFFFFFFFF)
        return size+'PLTE'+s+crc

def random(N_colors, background=(0,0,1), borders=(0,0,0),alphas=[0]):
    colors = set()
    while len(colors) < N_colors:
        colors.add((choice(WEB_SAFE_COLORS), choice(WEB_SAFE_COLORS), choice(WEB_SAFE_COLORS)))
    colors = [background,borders]+list(colors)
    return ColorScheme(colors,alphas)
def fade(steps=1, left=(255,0,0), right=(0,0,255), background=(0,0,1), borders=(0,0,0)):
    colors = [background,borders]
    if steps == 1:
        #just return averages
        sr,sg,sb = [(r-l)/(2) for r,l in zip(right,left)]
        r, g, b = left
        r += sr
        g += sg
        b += sb
    else:
        #step
        sr,sg,sb = [(r-l)/(steps-1) for r,l in zip(right,left)]
        r, g, b = left
    colors.append((r,g,b))
    for i in xrange(1,steps-1):
        r += sr
        g += sg
        b += sb
        colors.append((r,g,b))
    colors.append(right)
    return ColorScheme(colors)
    

def tRNS(alphas):
    """ Pack a list of alpha values into a PNG tRNS chunk
        The alpha value for class i == alpha[i], and should be <= 255
        255 == opaque
          0 == transparent
        >>> tRNS( [0] )
    """
    if alphas == NO_tRNS:
        return ''
    if not alphas:
        return '\x00\x00\x00\x01tRNS\x00@\xe6\xd8f' #background = 0
    #trns = array(UNSIGNED_ITEM_TYPES[1])
    #try:
    #    trns.fromlist(alphas)
    #except OverflowError:
    #    raise OverflowError, "Alpha value is greater than the maximum (255)"
    #s = trns.tostring()
    s = alphas
    size = pack('!I', len(s))
    crc = pack('!I', crc32('tRNS'+s) & 0xFFFFFFFF)
    return size+'tRNS'+s+crc
    
def PLTE(colors):
    """ Pack a list of colors into a PNG PLTE chunk
        >>> PLTE( [(0,0,1),(0,0,0),(255,0,0),(0,0,255)] )
    """
    #s = ''.join([pack('!3B',r&0xFF,g&0xFF,b&0xFF) for r,g,b in colors])
    s = ''.join(colors)
    size = pack('!I', len(s))
    crc = pack('!I', crc32('PLTE'+s) & 0xFFFFFFFF)
    return size+'PLTE'+s+crc
    

if __name__=='__main__':
    pass
    #p = PseudoColorScheme(n=5)
    #print p.PLTE
