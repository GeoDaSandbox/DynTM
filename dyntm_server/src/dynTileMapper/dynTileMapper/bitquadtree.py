import array
from bitmap import BitMap
def bin(x,depth=8):
    l = []
    for i in xrange(depth):
        l.append(x%2)
        x=x>>1
    l.reverse()
    return l
def bits2int(l):
    assert len(l)==8
    a,b,c,d,e,f,g,h = l
    return (a<<7)|(b<<6)|(c<<5)|(d<<4)|(e<<3)|(f<<2)|(g<<1)|(h)

class QTree:
    def __init__(self):
        self.child = Branch()
    def __getitem__(self,*args):
        return self.child
    @staticmethod
    def findPath(z,x,y):
        maxIndex = 2**z-1
        if x<0 or y<0 or x>maxIndex or y>maxIndex:
            raise IndexError,"At zoomlevel %d the max x or y is %d"%(z,maxIndex)
        path = []
        x,y = bin(x,z),bin(y,z)
        path = zip(x,y)
        return path
    def set(self,zoom,X,Y,leaf=False):
        if zoom == 0:
            return self.child
        path = self.findPath(zoom,X,Y)
        node = self[0,0]
        last = path.pop()
        for x,y in path:
            if node.isleaf:
                print "reached unexpected leaf"
                return node
            if node[x,y]:
                node = node.getChild(x,y)
            else:
                node.addBranch(x,y)
                node = node.getChild(x,y)
        x,y = last
        if leaf:
            node.addLeaf(x,y)
            node.getChild(x,y).setPath(zoom,X,Y)
        else:
            node.addBranch(x,y)
        return node.getChild(x,y)
    def get(self,zoom,x,y):
        path = self.findPath(zoom,x,y)
        node = self[0,0]
        for x,y in path:
            if node[x,y]:
                node = node.getChild(x,y)
                if node.isleaf:
                    #print "reached unexpected leaf"
                    return node
            else:
                return None
        return node
class Branch(BitMap):
    def __init__(self,dateType='B',init='\x00'):
        BitMap.__init__(self,init)
        self.isleaf=False
        self.__children = [None,None,None,None]
    def getChild(self,x,y):
        if self[x,y]:
            return self.__children[y*2+x]
    def getChildren(self):
        return [c for c in self.__children if c]
    def addBranch(self,x,y):
        if not self[x,y]:
            self.__children[y*2+x] = Branch()
            self[x,y] = True
    def addLeaf(self,x,y):
        if not self[x,y]:
            self.__children[y*2+x] = Leaf()
            self[x,y] = True
    def tostring(self):
        b = array.array.__getitem__(self,0)
        b = bin(b,8)
        leafs = []
        for x in [0,1]:
            for y in [0,1]:
                if self[x,y]:
                    idx = y*2+x
                    if self.__children[idx].isleaf:
                        b[idx] = 1
                        leafs.append(self.__children[idx].tostring())
        b = str(bits2int(b))
        b = b+'|'+';'.join(leafs)
        return b
class Leaf(object):
    __slots__=('isleaf','id','path')
    def __init__(self):
        self.isleaf=True
        self.id = -99
        self.path=(0,0,0)
    def setPath(self,zoom,x,y):
        self.path=(zoom,x,y)
    def __getstate__(self):
        return "%d:%d:%d:%d"%(self.id,self.path[0],self.path[1],self.path[2])
    def __setstate__(self,s):
        id,zoom,x,y = s.split(':')
        self.isleaf=True
        self.id = int(id)
        self.setPath(int(zoom),int(x),int(y))

def printquad(q):
    z = 0
    print 'zoom: ',z
    node = q.child
    node.prettyPrint()
    children = []
    children.extend(node.getChildren())
    while children:
        n = len(children)
        z+=1
        print '================='
        print 'zoom: ',z
        for i in range(n):
            node = children.pop(0)
            if node.isleaf:
                print
                print "LEAF: ",node.id
            else:
                print
                node.prettyPrint()
                children.extend(node.getChildren())
    


if __name__=='__main__':
    import cPickle
    q = QTree()
    z=4
    for i in range(2**z):
        leaf = q.set(z,i,i,leaf=True)
        leaf.id=(i+1)**2
    printquad(q)
    #s = cPickle.dumps(q)
    #q2 = cPickle.loads(s)
