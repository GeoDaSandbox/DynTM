import os.path
from abstractmodel import AbstractModel
#from pysal import dbfreader
import pysal
from dynTileMapper import mapTools
from dynTileMapper import pypng
import yaml
from cStringIO import StringIO
import cProfile
import base64
import time
from dynTileMapper import bitquadtree
from collections import deque
import sys
try:
    if sys.platform == 'win32':
        multiprocessing = False
    else:
        import multiprocessing
except ImportError:
    multiprocessing = False

PREVIEW_SIZE = (512,512)

def newProp(fnc):
    return property(**fnc())
class M_DyMaps2(yaml.YAMLObject,AbstractModel):
    """ Data Model for Map Loader
        Supports YAML dumping and loading
    """
    TAGS = ['geoData','variableNames','idVariable','mapScales','mapPng','source','notes','name','scales','cacheFile'] #'cacheSize']
    # Dictionary to hold model data
    __modelData = {}
    __db = None #keep the DB around if we open it
    __mapObj = None #same
    __size = (0,0)
    #__tileCache = {}
    __qtree = bitquadtree.QTree()
    def __iter__(self):
        return self.next()
    def next(self):
        for key in self.TAGS:
            yield key,self.__getattribute__(key)
    def absProp(tag):
        if not issubclass(type(tag),basestring):
            return None
        def fget(self,tag=tag):
            if tag in self.__modelData:
                return self.__modelData[tag]
            else:
                return ''
        def fset(self,value,tag=tag):
            self.__modelData[tag] = value
            self.update(tag)
        def fdel(self,tag=tag):
            if tag in self.__modelData:
                del self.__modelData[tag]
        del tag
        return property(**locals())
    source = absProp('source')
    name = absProp('name')
    notes = absProp('notes')
    variableNames = absProp('variableNames')
    idVariable = absProp('idVariable')
    #mapPng = absProp('mapPng')
    mapSize = absProp('mapSize')
    scales = absProp('scales')
    ids = absProp('ids')
    cLng = absProp('cLng')
    cLat = absProp('cLat')
    minx, miny, maxx, maxy = absProp('minx'), absProp('miny'), absProp('maxx'), absProp('maxy')
    gmerc_bounds = absProp('gmerc_bounds')
    overview_typ = absProp('overview_typ')
    overview_dat = absProp('overview_dat')
    overview_width = absProp('overview_width')
    overview_height = absProp('overview_height')
    #cacheSize = absProp('cacheSize')

    @newProp
    def size():
        def fget(self):
            return self.__size
        def fset(self,v):
            if self.__size != v:
                self.__size=v
                self.update('mapPng',changeState=False)
        return locals()
    @newProp
    def mapScales():
        def fget(self):
            if not self.geoData or not os.path.exists(self.geoData):
                return ''
            return self.__mapObj.getZoomLevels()
        return locals()
    @newProp
    def sourceProj():
        def fget(self):
            if self.__mapObj:
                return self.__mapObj.projection
            else:
                return ''
        return locals()
    def mapPngZoom(self,z):
        return self.__mapObj.pngZoom(z)
    @newProp
    def mapPng():
        tag='mapPng'
        def fget(self,tag=tag):
            if not self.geoData or not os.path.exists(self.geoData):
                return ''
            if type(self.idVariable) == int:
                var = self.variableNames[self.idVariable]
            else:
                var = None
            self.__mapObj.idVar = var
            self.__mapObj.size = self.__size
            return self.__mapObj.png
        del tag
        return locals()
    @newProp
    def geoData():
        tag='geoData'
        def fget(self,tag=tag):
            if tag in self.__modelData:
                return self.__modelData[tag]
            else:
                return ''
        def fset(self,value,tag=tag):
            if os.path.exists(value) and not os.path.isdir(value):
                self.__modelData[tag] = value
                self.__loadDataFile()
                self.__mapObj = mapTools.MapScriptObj(value,self.__size)
                self.__modelData['projString'] = self.__mapObj.projection
                center = self.__mapObj.WGScenter
                self.__modelData['cLng'] = center['lng']
                self.__modelData['cLat'] = center['lat']
                self.__modelData.update(self.__mapObj.WGSbounds)
                b = self.__mapObj.bounds
                self.__modelData['gmerc_bounds'] = [b.minx,b.miny,b.maxx,b.maxy]
                if not self.cacheFile:
                    self.cacheFile = value[:-4]+'_cache.csv'
            else:
                self.__modelData[tag] = False
            self.update(tag)
            self.update('mapPng')
            self.update('mapScales')
        def fdel(self,tag=tag):
            del self.__modelData[tag]
        del tag
        return locals()
    @newProp
    def cacheFile():
        tag='cacheFile'
        def fget(self,tag=tag):
            if tag in self.__modelData:
                return self.__modelData[tag]
            else:
                return ''
        def fset(self,value,tag=tag):
            if not os.path.isdir(value):
                self.__modelData[tag] = value
                #self.checkCache()
            else:
                self.__modelData[tag] = False
            self.update(tag)
            #self.update('cacheSize')
        def fdel(self,tag=tag):
            del self.__modelData[tag]
        del tag
        return locals()
    def getByTag(self,tag):
        return self.__getattribute__(tag)
    def __loadDataFile(self):
        if self.geoData[-4:] == '.shp':
            dbfName = self.geoData[:-4]+'.dbf'
            db = pysal.open(dbfName,'r')
            self.__db = db
            self.variableNames = db.header[:]
        else:
            return None
    def verbose(self):
        print self.__modelData
    def verify(self):
        """ Return True is model is ready to run """
        D,S,I,C = False,False,False,False
        if self.geoData and os.path.exists(self.geoData):
            D = True
        if self.scales:
            S = True
        if type(self.idVariable) == int:
            I = True
        if self.cacheFile:
            C = True
        if D and S and I and C:
            return True
        return False
    def reset(self):
        self.__modelData = {}
        self.update()
        self.SetModified(False)
    def run(self,pulse=None):
        self.__mapObj.size = (256,256)
        global t
        global q
        t = self.__mapObj.tiler
        q = self.__qtree
        if multiprocessing:
            pool = multiprocessing.Pool()
        else:
            print "no MP"
            class fakePool:
                map = map
            pool = fakePool()
        cont = True
        t0 = time.time()
        out = open(self.cacheFile,'w')
        out.write('Zoom,X,Y,tile_type,optTile(PNG)\n')
        totCount = 0
        
        for z in self.scales:
            estCount = 0
            realCount = 0
            queue = deque()
            leftx,boty,rightx,topy,zoom = t.gTileBounds(zoom=z)
            for x in xrange(leftx,rightx+1):
                for y in xrange(topy,boty+1):
                    try:
                        node = q.get(z,x,y)
                        estCount +=1
                        if node:
                            if not node.isleaf:
                                #If node isleaf it is blank or single, don't render children
                                queue.append((x,y,z))
                        else:
                            queue.append((x,y,z))
                    except IndexError:
                        pass
                        #print "IndexError",x,y,z,"is not valid"
            r = pool.map(processTile,queue)
            for x,y,zoom,tileType,tile in r:
                realCount+=1
                if tileType in 'AB':
                    node = q.set(zoom,x,y,leaf=True)
                if tileType in 'CD':
                    node = q.set(zoom,x,y,leaf=False)
                    out.write( "%d,%d,%d,%s,%s\n"%(zoom,x,y,tileType,tile) )
            cont = pulse(realCount)
            print z,"QTree Saved: %d"%(estCount-realCount)
            totCount+=realCount
        #for z in tiles:
        #    if tiles[z]:
        #        #work on chunks of 100 tiles
        #        for start in range(0,len(tiles[z]),20):
        #            r = pool.map(processTile,tiles[z][start:start+100])
        #            for x,y,zoom,tileType,tile in r:
        #                cont = pulse(1)
        #                out.write( "%d,%d,%d,%s,%s\n"%(zoom,x,y,tileType,tile) )
        #                if not cont:
        #                    out.close()
        #                    return False
        totTime = time.time()-t0
        print "Tiles: %d\t Total Time: %f\t Time/Tile:%f"%(totCount,totTime,totTime/totCount)
        pulse(-1)
        out.close()
        return True

    def save_to_ms(self,path):
        self.__mapObj.saveToMS(path,yaml.dump(self))

    ### BEGIN YAML SUPPORT
    yaml_tag = u'!DyMapConfig'
    @classmethod
    def from_yaml(cls,loader,node):
        """ >>> yaml.load('!DyMapConfig {dataFile: file}\n')
            <__main__.M_DyMaps2 object at 0x1585bf70>
        """
        data = loader.construct_mapping(node)
        c = cls()
        c.__modelData = data
        c.geoData = c.__modelData['geoData']
        c.cacheFile = c.__modelData['cacheFile']
        c.SetModified(False)
        return c
    @classmethod
    def to_yaml(cls,dumper,self):
        """ >>> model = M_DyMaps2()
            >>> model.dataFile = 'somefile.shp'
            >>> yaml.dump(model)
            '!DyMapConfig {dataFile: file}\n'
        """
        #self.__modelData['ids'] = self.__mapObj.ids
        self.__modelData['ids'] = ','.join(map(str,self.__mapObj.ids))

        ##GENERATE Overview
        old_size = self.__size
        self.__mapObj.size = PREVIEW_SIZE
        typ,dat,width,height = processOverview(self.__mapObj.png)
        self.__modelData['overview_typ'] = typ
        self.__modelData['overview_dat'] = dat
        self.__modelData['overview_width'] = width
        self.__modelData['overview_height'] = height
        self.__mapObj.size = old_size
        #END Overview

        node = dumper.represent_mapping(cls.yaml_tag,self.__modelData)
        self.SetModified(False)
        return node
    ### END YAML SUPPORT

def processOverview(png):
    png = StringIO(png)
    png = pypng.png.PNG(png)
    tileType,tile = pypng.optTile.optTile(png)
    return (tileType, tile, png.data['IHDR']['width'], png.data['IHDR']['height'])
def processTile(tup):
    x,y,zoom = tup
    png = t.gTileDraw(x,y,zoom)
    #o = open('%d_%d_%d.png'%(x,y,zoom),'wb')
    #o.write(png)
    #o.close()
    png = StringIO(png)
    png = pypng.png.PNG(png)
    tileType,tile = pypng.optTile.optTile(png)
    return (x,y,zoom,tileType,tile)
if __name__=='__main__':
    f = open('/Users/charlie/Documents/data/stl_hom/stl_hom.yaml','r')
    m = yaml.load(f.read())
    f.close()
    def p(*args):
        return True
    m.run(p)
