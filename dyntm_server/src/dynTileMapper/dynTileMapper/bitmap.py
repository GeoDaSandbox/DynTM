import array
import zlib
import random
from math import ceil

MASK = {0:0x01, 1:0x02, 2:0x04, 3:0x08, 4:0x10, 5:0x20, 6:0x40, 7:0x80}
class BitMap(array.array):
    """Bin Map holds n*n True/False values
        it is indexed with an x,y values.
        max X = n
        max Y = n
        it is initialized to False.
        >>> B = BitMap(n=2048)
        >>> B[215,24] (x=215,y=24)
        Flase
        >>> B[215,24] = True
        >>> B[0,0] = True
        >>> B[2047,2047] #max index
        Flase
    """
    def __new__(cls,*args,**kwargs):
        return super(BitMap,cls).__new__(cls,'B')
    def __init__(self,s=None,n=2048):
        array.array.__init__(self)
        if s:
            array.array.fromstring(self,s)
            slen = len(s)
            self.n = int((slen*8)**0.5)
        else:
            if n < 4:
                raise TypeError,'Min Size is 4x4'
            slen = int(ceil((n**2)/8.0))
            array.array.fromstring(self,'\x00'*slen)
            self.n = n #size of one side
    def __getitem__(self,key):
        try:
            n = self.n
            row,col = key
            if row >= n or col >=n:
                raise IndexError, 'array index out of range'
            idx = row*n+col
            byteIndex = idx/8
            #print byteIndex,':',idx%8
            byte = array.array.__getitem__(self,byteIndex)
            bitMask = MASK[idx%8]
            if byte&bitMask:
                return True
            else:
                return False
        except:
            raise
            raise KeyError,'Please index with x,y'
    def __setitem__(self,key, value):
        try:
            n = self.n
            row,col = key
            if row >= n or col >=n:
                raise IndexError, 'array index out of range'
            idx = row*n+col
            byteIndex = idx/8
            bitMask = MASK[idx%8]
            byte = array.array.__getitem__(self,byteIndex)
            if value:
                if not byte&bitMask:
                    array.array.__setitem__(self,byteIndex, byte+bitMask )
            else:
                if byte&bitMask: #allready true, make false
                    array.array.__setitem__(self,byteIndex, byte-bitMask )
        except:
            raise
            raise KeyError,'Please index with x,y'
    @staticmethod
    def byte2count(byte):
        if not byte:
            return 0
        elif byte == 0xff:
            return 8
        else:
            return  (byte & 0x01) + ((byte >> 1) & 0x01) + \
                    ((byte >> 2) & 0x01) + ((byte >> 3) & 0x01) + \
                    ((byte >> 4) & 0x01) + ((byte >> 5) & 0x01) + \
                    ((byte >> 6) & 0x01) + ((byte >> 7) & 0x01)
    def count(self):
        "return the number of 'True' elements"
        f = self.byte2count
        return sum(map(f,self))
    def random_test(self):
        X = random.sample(xrange(2048),200)
        Y = random.sample(xrange(2048),200)
        for x in X:
            for y in Y:
                self[x,y] = True
    def compress(self):
        return zlib.compress(self.tostring())
    def prettyPrint(self):
        n = self.n
        for row in xrange(n):
            s='\t'.join([str(self[row,col]) for col in xrange(n)])
            print s
    @classmethod
    def fromz(cls,z):
        s = zlib.decompress(z)
        return cls(s)
class BitMap_RO:
    "A READ_ONLY bitMap, supports FAST read"
    def __init__(self,s):
        self.s = s
        slen = len(s)
        self.n = int((slen*8)**0.5)
    def __getitem__(self,key):
        try:
            n = self.n
            row,col = key
            if row >= n or col >=n:
                raise IndexError, 'array index out of range'
            idx = row*n+col
            byteIndex = idx/8
            bitMask = MASK[idx%8]
            byte = ord(self.s[byteIndex])
            if byte&bitMask:
                return True
            else:
                return False
        except:
            raise
            raise KeyError,'Please index with x,y'
    def __setitem__(self,key, value):
        raise NotImplementedError,'BitMap_RO is READ ONLY!'
    @classmethod
    def fromz(cls,z):
        s = zlib.decompress(z)
        return cls(s)

def BitMap_test():
    import random
    b = BitMap(n=2050)
    X = random.sample(xrange(2048),200)
    Y = random.sample(xrange(2048),200)

    for x in X[:100]:
        for y in Y[:100]:
            b[x,y] = True
            assert b[x,y] == True
    assert b.count()==10000
    bRO = BitMap_RO(b.tostring())

    for x in X[100:]:
        for y in Y[100:]:
            assert b[x,y] == False

    for x in X[:100]:
        for y in Y[:100]:
            assert b[x,y] == True
            assert bRO[x,y] == True
            b[x,y] = False
            assert b[x,y] == False
    assert b.count()==0
    
def scales():
    print "Zoom\t\tWxH\t\tTotal Size"
    for i in range(20):
        print "%d\t\t%d\t\t%d"%(i, 2**i , 4**i)
if __name__=="__main__":
    import cProfile
    cProfile.run('BitMap_test()')
    f = open('test.dat','wb')
    b = BitMap(n=5000)
    X = random.sample(xrange(2048),200)
    Y = random.sample(xrange(2048),200)
    for x in X:
        for y in Y:
            b[x,y] = True
    f.write(zlib.compress(b.tostring()))
    f.close()
    f = open('test.dat','rb')
    z = f.read()
    f.close()
    s = zlib.decompress(z)
    ntest = 100
    xy = [(random.randint(0,2027),random.randint(0,2027)) for i in range(ntest)]
    cProfile.run('r = [ BitMap_RO(s)[x,y] for x,y in xy]')
    cProfile.run('r2 = [ BitMap(s)[x,y] for x,y in xy]')
