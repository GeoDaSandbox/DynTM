import pysal
import os

DEPTH = 24 #rrggbb = redByte,greenByte,blueByte
MAXCOLOR = 2**DEPTH-1
ID_OFFSET = 2 # 0==background,1==borders

class ColorError(Exception):
    """Exception raised for errors in Color Value.

    Attributes:
        value -- integer value being turned into a color
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        if self.value > MAXCOLOR:
            return "Value: %d, is too large for the current bitdept: %d"%(self.value,DEPTH)
        else:
            return "Something is wrong with the input value: %r"%(self.value)
def toColor(n):
    """We need to encode the ID into three 8 bit ints.
    This is done by going first to a 6 digit HEX number,
    then we divid the number into 3 pairs of 2-digit hex 
    numbers and convert them back to deci.  This ensures
    that none of the sets exceeds the value of 255 the
    limit for an 8bit int."""
    color = ('%X'%(n+ID_OFFSET)).rjust(6,'0')
    if not len(color) == 6:
        raise ColorError(n)
    else:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        return '%.3d %.3d %.3d'%(r,g,b)

class Classifier:
    """ Simple Map Classifier
        c = Classifier(shapePath,shapeName)
        c.SetUID('IdName')
    """
    def __init__(self,shpPath,shpName):
        filename = os.path.join(shpPath,shpName+'.dbf')
        self.db = db = pysal.open(filename,'r')
        self.head = db.header
        #self.spec = db.spec
        self.UID = None
        self.ids = None
        self.ids_unsorted = []
    def SetUID(self,field,forceUnique=True):
        idsUS = self.ids_unsorted
        if field in self.head:
            try:
                i = self.head.index(field)
            except ValueError:
                print self.head
                raise
            ids = set()
            for row in self.db:
                id = row[i]
                if id in ids and forceUnique:
                    raise StandardError('Not a Unique ID')
                else:
                    ids.add(id)
                    idsUS.append(id)
            ids = list(ids)
            ids.sort()
            self.UID = field
            self.ids = ids
        else:
            self.UID = None
            self.ids = None
    def __repr__(self):
        if self.UID and self.ids:
            pass
        else:
            raise StandardError("UID not set")
        s = "CLASSITEM '%s'"%self.UID
        for i,id in enumerate(self.ids):
            try:
                color = toColor(i)
            except ColorError:
                raise
            s += """
                CLASS
                    NAME '%(UID)s = %(id)s'
                    EXPRESSION '%(id)s'
                    OUTLINECOLOR 0 0 1
                    COLOR %(color)s
                END"""%{'UID':self.UID,'id':id,'color':color}
        return s
    def __call__(self):
        return self.__repr__()
    def toDBF(self,fname):
        if self.UID and self.ids:
            pass
        else:
            raise StandardError("UID not set")
        db = pysal.open(fname,'w')
        db.header = ['dtmValue']
        db.field_spec = [('C',7,0)]
        for id in self.ids_unsorted:
            i = self.ids.index(id)+ID_OFFSET
            db.write(['#%0.6X'%i])
        db.close()
            

if __name__ == '__main__':
    path = '../../../../pysal/trunk/pysal/data/'
    fname = 'co34_d00'
    c = Classifier(path,fname)
    c.SetUID('CO34_D00_I')
