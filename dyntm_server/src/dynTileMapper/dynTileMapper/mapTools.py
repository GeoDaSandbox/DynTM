### Standard Import
import sys,os
import os.path
if sys.platform == 'win32':
    os.putenv('PROJ_LIB',os.path.join(sys.prefix,'PROJ','NAD'))
import tempfile,atexit
### Custom Imports, these need to be installed.
import mapscript as ms
assert ms.msGetVersionInt() >= 50200 #require 5.2.0 or above
assert 'OUTPUT=PNG' in ms.msGetVersion() #require PNG support
assert 'INPUT=SHAPEFILE' in ms.msGetVersion() #require SHAPEFILE support
from osgeo import osr
import pysal
### Local imports. included
from tileMaker.common import MAPFILE
from tileMaker.classifier import Classifier
from tileMaker.tiler import Tiler

#GMERC = ms.projectionObj('init=epsg:900913')
GMERC = ms.projectionObj('init=epsg:3857')
WGS84 = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs '
UTM31 = '+proj=utm +zone=31 +ellps=WGS84 +datum=WGS84 +units=m +no_defs '
DEFAULT_SOURCE_PROJ = WGS84
ID_OFFSET = 2 # 0==background,1==borders
DEFAULT_COLOR = '128 60 200'

class MapScriptObj(object):
    """ A Pythonic API for working with shapefiles in mapscript,
        >>> m = MapScriptObj('path/to/file.shp')
        >>> m.projection
        '+proj=utm +zone=12 +ellps=clrk66 +units=m +no_defs '
        >>> m.png
        '\x89PNG\r\n\x1a\n\x00\x00\x00\r....'
    """
    def __init__(self, shpfile, size=(256,256), idVariable=None):
        self.__pathToShapeFile = None
        self.__files = []
        self.__workSpace = tempfile.mkdtemp()
        #print 'Workspace = ',self.__workSpace
        self.__projection = None
        self.__targetProj = GMERC
        self.__idVariable = None
        self.width = 0
        self.height = 0
        self.size = size
        self.mapObj = shpfile
        self.idVar = idVariable
        atexit.register(self.close)
    def __setTargetProj(self,value):
        try:
            self.__targetProj = ms.projectionObj(value)
        except:
            raise TypeError,"%s, is not a valid projection string!"%(str(value))
    def __getTargetProj(self):
        return self.__targetProj
    def __setProjection(self,value):
        if not value:
            shapePath, shapeName = os.path.split(self.__pathToShapeFile)
            shapeName = shapeName.split('.')[0]
            prjName = shapeName+'.prj'
            prjFile = os.path.join(shapePath,prjName)
            if os.path.exists(prjFile):
                f = open(prjFile,'r')
                s = f.read()
                f.close()
                srs = osr.SpatialReference()
                errCode = srs.ImportFromWkt(s)
                #print "ProjError: ",errCode
                self.__projection = srs.ExportToProj4()
                if not self.__projection:
                    #self.__projection = 'init=epsg:900913'
                    self.__projection = 'init=epsg:3857'
            else:
                self.__projection = DEFAULT_SOURCE_PROJ
        if value:
            self.__projection = value
    def __getProjection(self):
        if not self.__projection:
            self.__setProjection(None)
            return self.__projection
        else:
            return self.__projection
    def __setSize(self,value):
        width,height = value
        self.width = width
        self.height = height
    def __getSize(self):
        return "%d %d"%(self.width,self.height)
    def __setMapObj(self,value):
        if os.path.exists(value):
            self.__pathToShapeFile = value
            iShp = value
            oShp = os.path.join(self.__workSpace,'dtm.shp')
            iShx = value.rsplit('.',1)[0]+'.shx'
            oShx = os.path.join(self.__workSpace,'dtm.shx')
            iQix = value.rsplit('.',1)[0]+'.qix'
            oQix = os.path.join(self.__workSpace,'dtm.qix')
            if os.path.exists(self.__workSpace):
                for infile,outfile in [(iShp,oShp),(iShx,oShx),(iQix,oQix)]:
                    if os.path.exists(infile):
                        i = open(infile,'rb')
                        o = open(outfile,'wb')
                        o.write(i.read())
                        i.close()
                        o.close()
                        self.__files.append(outfile)
        else:
            raise IOError,"File does not exsist: %s:"%value
    def __setIDVar(self,id):
        if self.__pathToShapeFile:
            shapePath, shapeName = os.path.split(self.__pathToShapeFile)
            shapeName = shapeName.split('.')[0]
            dbfPath = os.path.join(shapePath,shapeName+'.dbf')
            db = pysal.open(dbfPath,'r')
            if id in db.header:
                self.__idVariable = id
            elif not id:
                self.__idVariable = ''
            else:
                db.close()
                raise KeyError,'%s, is not a valid field'%(id)
            db.close()
            if self.__idVariable:
                c = Classifier(shapePath,shapeName)
                c.SetUID(self.idVar,False)
                oDbf = os.path.join(self.__workSpace,'dtm.dbf')
                c.toDBF(oDbf)
                if oDbf not in self.__files:
                    self.__files.append(oDbf)
                self.__ids = c.ids
    def __getIDVar(self):
        return self.__idVariable

    def save_to_mapfile(self,out_path):
        path = self.__pathToShapeFile
        shapePath, shapeName = os.path.split(path)
        shapeName = shapeName.split('.')[0]
        shpfile = ms.shapefileObj(path,-1) # "value of -1 to open an existing shapefile"-ms.docs
        #print self.projection
        src_prj = ms.projectionObj(self.projection)
        shpfile.bounds.project(src_prj,self.targetProj)
        mapobj = ms.fromstring(MAPFILE%{'shapePath':shapePath,'shapeName':shapeName,'color':'[dtmValue]','projString':self.projection,'size':self.size})
        mapobj.extent = shpfile.bounds
        mapobj.save(out_path)

    def __getMapObj(self):
        path = self.__pathToShapeFile
        shapePath, shapeName = os.path.split(path)
        shapeName = shapeName.split('.')[0]
        shpfile = ms.shapefileObj(path,-1) # "value of -1 to open an existing shapefile"-ms.docs
        #print self.projection
        src_prj = ms.projectionObj(self.projection)
        shpfile.bounds.project(src_prj,self.targetProj)
        if not self.idVar:
            mapobj = ms.fromstring(MAPFILE%{'shapePath':shapePath,'shapeName':shapeName,'color':DEFAULT_COLOR,'projString':self.projection,'size':self.size})
        else:
            mapobj = ms.fromstring(MAPFILE%{'shapePath':self.__workSpace,'shapeName':'dtm','color':'[dtmValue]','projString':self.projection,'size':self.size})
            
        mapobj.extent = shpfile.bounds
        return mapobj
    size = property(fget=__getSize,fset=__setSize)
    idVar = property(fget=__getIDVar,fset=__setIDVar)
    projection = property(fget=__getProjection,fset=__setProjection)
    targetProj = property(fget=__getTargetProj,fset=__setTargetProj)
    mapObj = property(fget=__getMapObj,fset=__setMapObj)
    @property
    def ids(self):
        return self.__ids
    @property
    def WGSbounds(self):
        x = self.bounds.minx
        y = self.bounds.miny
        p = ms.pointObj(x,y)
        assert p.project(GMERC,ms.projectionObj(WGS84)) == 0
        X = self.bounds.maxx
        Y = self.bounds.maxy
        P = ms.pointObj(X,Y)
        assert P.project(GMERC,ms.projectionObj(WGS84)) == 0
        
        return {'minx':p.x,'miny':p.y,'maxx':P.x,'maxy':P.y}
    @property
    def WGScenter(self):
        center = self.bounds.getCenter()
        center.project(GMERC,ms.projectionObj(WGS84))
        return {'lng':center.x,'lat':center.y}
    @property
    def bounds(self):
        return self.mapObj.extent
    def getZoomLevels(self):
        t = Tiler(self.mapObj)
        return t.getScales()
    @property
    def png(self):
        mp = self.mapObj
        img = mp.draw()
        return img.saveToString()
    def pngZoom(self,z):
        print "init Tiler"
        t = Tiler(self.mapObj)
        print "find gTileBounds"
        leftx,boty,rightx,topy,zoom = t.gTileBounds(zoom=z)
        print "find center"
        meanX = int(round(sum([leftx,rightx])/2.0))
        meanY = int(round(sum([boty,topy])/2.0))
        print "drawTile"
        png = t.gTileDraw(meanX,meanY,z)
        return png
    @property
    def tiler(self):
        return Tiler(self.mapObj)
    def close(self):
        """This function cleans up our mess, it is bound with atexit.register,
            but no harm is done in calling it explicitly
        """
        if os.path.exists(self.__workSpace):
            while self.__files:
                f = self.__files.pop()
                os.remove(f)
            os.rmdir(self.__workSpace)
            print "cleaned up"
    def saveToMS(self,path,yml):
        for f in self.__files:
            if os.path.exists(f):
                i = open(f,'rb')
                o = open(os.path.join(path,os.path.basename(f)),'wb')
                o.write(i.read())
                o.close()
                i.close()
        ws = self.__workSpace
        self.__workSpace = ''
        self.mapObj.save(os.path.join(path,'dtm.map'))
        open(os.path.join(path,'dtm.yaml'),'w').write(yml)
        self.__workSpace = ws
    
if __name__=='__main__':
    #path = '../../../pysal/trunk/pysal/data/co34_d00.shp'
    path = '/Users/charlie/Documents/data/usa/usa.shp'
    path = '/var/maps/world/dtm.shp'
    #path = '/Users/charlie/Documents/data/tracts/ntracts_Dissolve.shp'
    mapObj = MapScriptObj(path)
    #mapObj.idVar = 'FIPS'
    mo = mapObj.mapObj
    #img = mapObj.png
    #f = open('out.png','wb')
    #f.write(img)
    #f.close()
