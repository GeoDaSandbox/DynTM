### System imports, Standard Libraries
import os
import sys
import zlib
import math
import struct
import base64

### Custom Imports, these need to be installed.
import mapscript as ms
assert ms.msGetVersionInt() >= 50200 #require 5.2.0 or above
assert 'OUTPUT=PNG' in ms.msGetVersion() #require PNG support
assert 'INPUT=SHAPEFILE' in ms.msGetVersion() #require PNG support
### Local imports. included
from common import SPHEREMERC_GROUND_SIZE,MAPFILE


WGS = ms.projectionObj('init=epsg:4326')
#GMERC = ms.projectionObj('init=epsg:900913')
GMERC = ms.projectionObj('init=epsg:3857')
ID_OFFSET = 2 # 0==background,1==borders

class Tiler:
    def __init__(self,mapobj):
        if issubclass(type(mapobj),basestring):
            mapobj = ms.mapObj(mapobj)
        self.map = mapobj
    def getScales(self):
        #print "Zoom: "
        scales = []
        for i in range(20):
            leftx,boty,rightx,topy,zoom = self.gTileBounds(zoom=i)
            scales.append((zoom,int((rightx+1-leftx)*(boty+1-topy))))
        return scales
    def calcExtent(self,x,y,zoom):
        """ 'Calculate the ground extents of the tile request.' - src/mapserv5/maptile.c"""
        box = ms.rectObj()
        zoomfactor = 2**zoom
        tilesize = SPHEREMERC_GROUND_SIZE / zoomfactor
        box.minx = (x * tilesize) - (SPHEREMERC_GROUND_SIZE / 2.0)
        box.maxx = ((x + 1) * tilesize) - (SPHEREMERC_GROUND_SIZE / 2.0)
        box.miny = (SPHEREMERC_GROUND_SIZE / 2.0) - ((y + 1) * tilesize)
        box.maxy = (SPHEREMERC_GROUND_SIZE / 2.0) - (y * tilesize)
        return box
        
    def gTileBounds(self,minx=None,miny=None,maxx=None,maxy=None,zoom=0):
        """ gTileBounds returns the bounds of the map in the gTile scheme. 
            note: gtBounds[4] should contain the zoom
        """
        zoomfactor = 2**zoom
        tilesize = SPHEREMERC_GROUND_SIZE / zoomfactor
        if not minx: minx = self.map.extent.minx
        if not miny: miny = self.map.extent.miny
        if not maxx: maxx = self.map.extent.maxx
        if not maxy: maxy = self.map.extent.maxy

        ## Left X
        #box.minx = (x * tilesize) - (SPHEREMERC_GROUND_SIZE / 2.0)
        leftx = math.floor((minx + (SPHEREMERC_GROUND_SIZE / 2.0)) / tilesize)
        ## Bottom Y .... Y's count up as you go south!
        #box.miny = (SPHEREMERC_GROUND_SIZE / 2.0) - ((y + 1) * tilesize)
        boty = math.ceil(((-1 * (miny - (SPHEREMERC_GROUND_SIZE / 2.0))) / tilesize) - 1)
        ## Right X
        #box.maxx = ((x + 1) * tilesize) - (SPHEREMERC_GROUND_SIZE / 2.0)
        rightx = math.ceil(((maxx + (SPHEREMERC_GROUND_SIZE / 2.0)) / tilesize) - 1)
        ## Top Y .... Top Y is 0!
        #box.maxy = (SPHEREMERC_GROUND_SIZE / 2.0) - (y * tilesize)
        topy = math.floor((-1 * (maxy - (SPHEREMERC_GROUND_SIZE / 2.0))) / tilesize)

        #print "\t - ",zoom,"\t#tiles: ",int((rightx+1-leftx)*(boty+1-topy))
        return map(int,[leftx,boty,rightx,topy,zoom])
    def zoomLevelDraw(self,gtBounds=None,zoom=None):
        if gtBounds: leftx,boty,rightx,topy,zoom = gtBounds
        elif not zoom==None: leftx,boty,rightx,topy,zoom = self.gTileBounds(zoom=zoom)
        else: return None
        for x in xrange(leftx,rightx+1):
            for y in xrange(topy,boty+1):
                self.gTileDraw(x,y,zoom)
    def gTileDraw(self,x,y,z,border=True):
        #print x,y,z
        m = self.map.clone()
        m.extent = self.calcExtent(x,y,z)
        if not border:
            m.getLayer(0).getClass(0).getStyle(0).outlinecolor.blue = -1
        img = m.draw()
        #path = os.path.join(self.outdir,'%d+%d+%d.png'%(x,y,z))
        #img.save(path)
        del m
        return img.saveToString()
        
            
def runTiler(shpfile,outdir,config,zoom=None):
    if not os.path.exists(shpfile):
        raise StandardError('Shape File: %s, does not exist!'%shpfile)
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    shapePath, shapeName = os.path.split(shpfile)
    shapeName = shapeName.split('.')[0]

    #c = Classifier(shapePath,shapeName)
    #c.CheckUID(config['IdName'])
    #mapProj = ms.projectionObj(config['projString'])

    shpfile = ms.shapefileObj(shpfile,-1) # "value of -1 to open an existing shapefile"-ms.docs
    bounds = shpfile.bounds
    return bounds
    bounds.project(mapProj,GMERC)
    mapobj = ms.fromstring(MAPFILE%{'shapePath':shapePath,'shapeName':shapeName,'classes':c(),'projString':config['projString']})
    mapobj.extent = bounds
    mapobj.draw().save('f.png')
    t = Tiler(mapobj,outdir,zoom)

    print "extents: "
    bounds.project(GMERC,WGS)
    print (bounds.maxx + bounds.minx) / 2
    print (bounds.maxy + bounds.miny) / 2

    return c,t

def main(config):
    required_keys = ['DataFile','TileDirectory']
    for k in required_keys:
        assert k in config

    if not 'Zoom' in config:
        c,t = runTiler(config['DataFile'],config['TileDirectory'],config)
    else:
        for z in config['Zoom']:
            c,t = runTiler(config['DataFile'],config['TileDirectory'],config,z)
    return c,t
    

if __name__=='__main__':
    import yaml
    try:
        options = sys.argv[1]
        f = open(options)
        config = yaml.safe_load(f)
        f.close()
        c,t = main(config)
    except IndexError:
        print "Usage: tiler.py options.yaml"
        config = {}
        config['IdName'] = 'FIPS'
        config['projString']='init=EPSG:4326'
        #a = runTiler('/Users/charlie/Documents/repos/geodacenter/pysal/trunk/pysal/weights/examples/usCounties/usa.shp','./',config)
        #a = runTiler('/Users/charlie/Documents/data/baghdad/baghdad.shp','./',config)
    except:
        raise

    #try:
    #    shpfile = sys.argv[1]
    #    outdir = sys.argv[2]
    #    if len(sys.argv) > 3: 
    #        zoom = sys.argv[3]
    #        print zoom
    #        if '-' in zoom:
    #            start,stop = map(int,zoom.split('-'))
    #            zoom = range(start,stop)
    #        else:
    #            zoom = [int(zoom)]
    #        for z in zoom:
    #            c,t = main(shpfile,outdir,z)
    #    else:
    #        c,t = main(shpfile,outdir,None)
    #except IndexError:
    #    print "Usage: tiler.py filename.shp path/to/output/dir [zoom_level]"
