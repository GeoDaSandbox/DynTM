"""
classification.py: Utilities for reading and creating classifications


Classifications classify a set of N regions into n classes.
     - There is no limit to N, though more then 1,000,000 becomes unreasonable.
        Each region costs 1 byte, so 1Million regions ~= 1MB.
        Though these compress well, AppEngine will choke on items larger then 1MB.

     - N is the number of REAL regions and does not include the background or borders
        Why: N == len(Shape File)
     - n is 1+max(classes)
        Why: n == len(Color Scheme)

     - n has an upper limit of 256 and,
        this includes the 2 de facto classes [background,borders].
        so the real limit is 254.
        This limit is imposed by the implementation, and helps ensure the tiles 
        are of reasonable size when delivered to the client.
        
     - Classifications are python lists.
        The 1st item in the list must be 0: The classID of the Background Region
        The 2nd item in the list must be 1: The classID of the Borders Region
        The 3rd item in the list identifies the classID of the 1st real region.
        The N+2'th item in the list identifies the classID of the N'th real region.
        There must be N+2 items in the list: (The total number of regions, plus bg+br)

     - Classification storage:
        Classifications are stored as compressed python array with typecode 'B'
        Notice that byteorder doesn't matter with typecode 'B'
        eg.
        >>> classification = [0,1,5,5,3,3,5,3,2,2,5,4,4,5,2,3]
        >>> N = len(classification) - 2
        >>> n = max(classification)+1
        >>> a = array.array('B')
        >>> a.fromlist(classification)
        >>> StoredClassification = zlib.compress(a.tostring())

     - Classifications are not Color Schemes
        and contain no color information.
        They simply bin the regions, colors are applied to the bins in a second step.
"""
import array
UNSIGNED_ITEM_TYPES = {array.array('B').itemsize:'B', array.array('H').itemsize:'H', array.array('I').itemsize:'I', array.array('L').itemsize:'L'}
import zlib
from random import randint,shuffle

class Classification(object):
    """ A convenience class for managing classifications """
    def __init__(self,zString):
        self.s = zlib.decompress(zString)
        self.a = array.array(UNSIGNED_ITEM_TYPES[1])
        self.a.fromstring(self.s)
        self.N = len(self.s) - 2
        self.n = max(self.a)+1
    @property
    def bytestring(self):
        return self.s
    @property
    def array(self):
        return self.a

def random(N,n=3):
    """ Return a random classification for N regions with n+2 classes"""
    classification = array.array(UNSIGNED_ITEM_TYPES[1])
    if n == 3:
        classification.fromlist( [0,1]+[2]*N )
    elif n>3 and n<257:
        p = (range(2,n)*((N/(n-2))+1))[:N]
        shuffle(p)
        classification.fromlist( [0,1]+p )
        #classification.fromlist( [0,1]+[randint(2,n-1) for i in xrange(N)] )
    else:
        raise TypeError, "n too small"
    return Classification(zlib.compress(classification.tostring()))
