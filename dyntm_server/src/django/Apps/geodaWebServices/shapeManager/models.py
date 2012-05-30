# Setup Django for testing outside a server environment.
if __name__=='__main__':
    import sys,os
    sys.path.append('/Users/charlie/Documents/repos/geodacenter/geodaWeb/trunk/django/Projects')
    os.environ['DJANGO_SETTINGS_MODULE']='gws_sqlite.settings'
# Standard Libaray
import os
import urllib
import hashlib
import tempfile
from cStringIO import StringIO
from math import floor,ceil
from cPickle import dump,load
# 3rd Party
import numpy
import pysal
import mapscript
import boto
# Custom
from gws_lib import db,config,s3_util,s3_multipart
# DynTM Imports
from dynTileMapper import mapTools
from dynTileMapper.tileMaker.tiler import Tiler
from dynTileMapper.pypng import png
from dynTileMapper.pypng.optTile import optTile

ID_OFFSET = 2 #background and borders
LOCAL_SHAPEFILE_PATH = '/var/shapefiles/'
AWS_SHP_BUCKET = "shapefiles"
BLANK = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
SPHEREMERC_GROUND_SIZE = (20037508.34*2)
WGS84 = mapscript.projectionObj('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs ')
GMERC = mapscript.projectionObj('init=epsg:3857')
import polygon_util

# Self Installing.  Make sure LOCAL_SHAPEFILE_PATH exists or that we have permission to create it.
if not os.path.exists(LOCAL_SHAPEFILE_PATH):
    try:
        os.mkdir(LOCAL_SHAPEFILE_PATH)
    except OSError,e:
        try:
            old = LOCAL_SHAPEFILE_PATH
            LOCAL_SHAPEFILE_PATH = '/var/tmp/shapefiles'
            if not os.path.exists(LOCAL_SHAPEFILE_PATH): os.mkdir(LOCAL_SHAPEFILE_PATH)
            print "WARNING: could not create LOCAL_SHAPEFILE_PATH: %s\n\tUsed alternate path: %s"%(old,LOCAL_SHAPEFILE_PATH)
        except:
            raise e

class Shapefile(db.Model):
    """ 
    Shapefile: This model represents an ESRI ShapeFile.
                An ESRI Shapefile is actaully 3 separate files.
                shp:  Contains the geometry
                shx:  An index that can be derived from the shp file
                dbf:  A standard DBF file that contains any data related to the geometry (record order must match)

    TODO: Add support for other projections.
          Currently we will assume that ALL shapefiles are projected as WGS84.

    NOTES: DBF Files are not stored with the Shapefile.

    Properties:
        key_name: str, The MD5 of the ".shp" portion of the shapefile. In UPPER case hex digest form.
        epsg: "4326" # WGS84 is assumed for all shpfiles.
        extent: [minx, miny, maxx, maxy]
        gmrec_extent: [minx, miny, maxx, maxy]
        n: Number of records
        public: If True, AWS S3 urls are publicly accessable.
        shp_url: AWS S3 url containing the SHP file.
        shx_url: AWS S3 url containing the SHX file.

    @Properties:
        shp_path: Returns a path on the local file system where the shpfile can be found.
        shx_path: Guaranteed to be shp_path.replace('.shp','.shx').  Calling either one guarantees the existence of both.
        dbf_path: The DBF is created on the file for use with DynTM Only. see shx_pth
        # Not implemented yet, needed?
        # shp: Returns the contents of the shpfile.
        # shx: Returns the contents of the shxfile.
        # dtmdbf: Returns the contents of the dbffile designed for use with DTM.
    """
    epsg = db.IntegerProperty()
    extent = db.ListProperty(item_type=float)
    gmerc_extent = db.ListProperty(item_type=float)
    n = db.IntegerProperty()
    shp_url = db.StringProperty()
    shx_url = db.StringProperty()
    aws_bucket = db.StringProperty()
    
    _installed = False
    def _install_local(self):
        base = os.path.join(LOCAL_SHAPEFILE_PATH,self.key_name)
        if os.path.exists(base+'.shp') and os.path.exists(base+'.shx') and os.path.exists(base+'.dbf') and os.path.exists(base+'.map'):
            self._installed = True
            return True
        else:
            try:
                shp = urllib.urlopen(self.shp_url)
                open(base+'.shp','wb').write(shp.read())
                shx = urllib.urlopen(self.shx_url)
                open(base+'.shx','wb').write(shx.read())
                dbf = pysal.open(base+'.dbf','w')
                dbf.header = ['dtmValue']
                dbf.field_spec = [('C',7,0)]
                for i in range(self.n):
                    dbf.write(["#%0.6X"%(i+ID_OFFSET)])
                dbf.close()

                #Install MapServer/MapScript .map file.
                mo = mapTools.MapScriptObj(base+'.shp').save_to_mapfile(base+'.map')

                self._installed = True
                return True
            except:
                if config.DEBUG:
                    raise
                else:
                    return False
    @property
    def shp_path(self):
        if self._installed or self._install_local():
            return os.path.join(LOCAL_SHAPEFILE_PATH,self.key_name)+'.shp'
        return ""
    @property
    def shx_path(self):
        if self._installed or self._install_local():
            return os.path.join(LOCAL_SHAPEFILE_PATH,self.key_name)+'.shx'
        return ""
    @property
    def dbf_path(self):
        if self._installed or self._install_local():
            return os.path.join(LOCAL_SHAPEFILE_PATH,self.key_name)+'.dbf'
        return ""
    @property
    def map_path(self):
        if self._installed or self._install_local():
            return os.path.join(LOCAL_SHAPEFILE_PATH,self.key_name)+'.map'
        return ""
    def polygons(self,zoom=0):
        pth = os.path.join(LOCAL_SHAPEFILE_PATH,self.key_name)+'.%d.json'%(zoom)
        if os.path.exists(pth):
            f = open(pth,'rb')
            ret = load(f)
            f.close()
            return ret
        else:
            dat = polygon_util.shp2json(self.shp_path,zoom)
            f = open(pth,'wb')
            ret = dump(dat,f)
            f.close()
        return dat
    def raw_png(self,x,y,z,border=True):
        left,top,right,bottom = self.gTileBounds(z)
        if not (left <= x and x <= right and top <= y and y <= bottom):
            return BLANK
        mp = self.map_path
        if mp:
            return Tiler(mp).gTileDraw(x,y,z,border)
        return None
    def raw_tile(self,x,y,z,border=True):
        left,top,right,bottom = self.gTileBounds(z)
        if not (left <= x and x <= right and top <= y and y <= bottom):
            return 'A','\x00'
        mp = self.map_path
        if mp:
            img = StringIO(Tiler(mp).gTileDraw(x,y,z,border))
            typ,dat = optTile(png.PNG(img),False)
            return typ,dat
        return None,None
    def gTileBounds(self,zoom):
        """ gTileBounds returns the bounds of the map in the gTile scheme. 
        """
        zoomfactor = 2**zoom
        tilesize = SPHEREMERC_GROUND_SIZE / zoomfactor
        minx,miny,maxx,maxy = self.gmerc_extent
        ## Left X
        #box.minx = (x * tilesize) - (SPHEREMERC_GROUND_SIZE / 2.0)
        leftx = floor((minx + (SPHEREMERC_GROUND_SIZE / 2.0)) / tilesize)
        ## Bottom Y .... Y's count up as you go south!
        #box.miny = (SPHEREMERC_GROUND_SIZE / 2.0) - ((y + 1) * tilesize)
        boty = ceil(((-1 * (miny - (SPHEREMERC_GROUND_SIZE / 2.0))) / tilesize) - 1)
        ## Right X
        #box.maxx = ((x + 1) * tilesize) - (SPHEREMERC_GROUND_SIZE / 2.0)
        rightx = ceil(((maxx + (SPHEREMERC_GROUND_SIZE / 2.0)) / tilesize) - 1)
        ## Top Y .... Top Y is 0!
        #box.maxy = (SPHEREMERC_GROUND_SIZE / 2.0) - (y * tilesize)
        topy = floor((-1 * (maxy - (SPHEREMERC_GROUND_SIZE / 2.0))) / tilesize)
        #print "\t - ",zoom,"\t#tiles: ",int((rightx+1-leftx)*(boty+1-topy))
        return map(int,[leftx,topy,rightx,boty])
        

def shp_info(shp,shx):
    """ Returns details about shapefile
        Aguments:
            shp: Binary contents of the .shp file.
            shx: Binary contents of the .shx file.
    """
    shpf = tempfile.NamedTemporaryFile('wb', suffix='.shp',delete=False)
    shpf.write(shp)
    shpf.close()
    shxf = open(shpf.name[:-3]+'shx','wb')
    shxf.write(shx)
    shxf.close()
    shp = pysal.open(shpf.name,'r')
    n = len(shp)
    shp.close()
    #Mapscript requires a DBF to read a shapefile.
    dbf = pysal.open(shpf.name[:-3]+'dbf','w')
    dbf.header = ['dtmValue']
    dbf.field_spec = [('C',7,0)]
    for i in range(n):
        dbf.write(["#%0.6X"%(i+ID_OFFSET)])
    dbf.close()

    shp = mapscript.shapefileObj(shpf.name)
    n = shp.numshapes
    x = shp.bounds.minx
    y = shp.bounds.miny
    X = shp.bounds.maxx
    Y = shp.bounds.maxy
    #wgs84 = mapscript.projectionObj('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs ')
    #gmerc = mapscript.projectionObj('init=epsg:3857')
    shp.bounds.project(WGS84,GMERC)
    gx = shp.bounds.minx
    gy = shp.bounds.miny
    GX = shp.bounds.maxx
    GY = shp.bounds.maxy
    os.remove(shpf.name)
    os.remove(shxf.name)
    return (n,[x,y,X,Y],[gx,gy,GX,GY])

def new_shapefile_from_parts(md5,shx):
    model = Shapefile.get_by_key_name(md5)
    if model:
        return False
    shx_url = s3_util.s3_upload(AWS_SHP_BUCKET,'public/%s.shx'%md5,shx,public=True,overwrite=True)
    s3client = s3_multipart.AWS_S3(config.aws_accesskeyid, config.aws_accesskey)
    return s3client.initiate_multipart_upload("public/"+md5+".shp", bucketName="shapefiles")
def upload_part_of_shapefile(md5,uploadId,partNum,data):
    s3client = s3_multipart.AWS_S3(config.aws_accesskeyid, config.aws_accesskey)
    return s3client.upload_part("public/"+md5+".shp", uploadId, partNum, data, bucketName="shapefiles")
def complete_multipart_upload(md5,uploadId,parts):
    s3client = s3_multipart.AWS_S3(config.aws_accesskeyid, config.aws_accesskey)
    location = s3client.complete_multipart_upload("public/"+md5+".shp", uploadId, parts, bucketName="shapefiles")
    s3 = s3_util.boto.connect_s3(config.aws_accesskeyid, config.aws_accesskey)
    s3.get_bucket("shapefiles").get_key("public/"+md5+".shp").set_acl('public-read')
    if location:
        model = new_shapefile_from_urls(location,location.replace('.shp','.shx'),md5)
        return model
    return False
        
def new_shapefile_from_urls(shp_url,shx_url, md5=False):
    shp = urllib.urlopen(shp_url)
    shp = shp.read()
    urlMD5 = hashlib.md5(shp).hexdigest().upper()
    if md5:
        if md5.upper() != urlMD5:
            return False #bad MD5
    shx = urllib.urlopen(shx_url).read()
    model = Shapefile(md5)
    model.aws_bucket = AWS_SHP_BUCKET
    model.public = True
    numregions,extent,gmerc_extent = shp_info(shp,shx)
    model.n = numregions
    model.extent = extent
    model.gmerc_extent = gmerc_extent
    model.shp_url = shp_url
    model.shx_url = shx_url
    model.put()
    return model
     
def new_shapefile(shp,shx):
    """ Returns a new Shapefile instance
        Aguments:
            shp: Binary contents of the .shp file.
            shx: Binary contents of the .shx file.
    """
    md5 = hashlib.md5(shp).hexdigest().upper()
    model = Shapefile.get_by_key_name(md5)
    if model:
        return model
    else:
        model = Shapefile(md5)
        model.aws_bucket = AWS_SHP_BUCKET
        model.public = True
        numregions,extent,gmerc_extent = shp_info(shp,shx)
        model.n = numregions
        model.extent = extent
        model.gmerc_extent = gmerc_extent
        shp_url = s3_util.s3_upload(AWS_SHP_BUCKET,'public/%s.shp'%md5,shp,public=True,overwrite=True)
        shx_url = s3_util.s3_upload(AWS_SHP_BUCKET,'public/%s.shx'%md5,shx,public=True,overwrite=True)
        if shp_url and shx_url:
            model.shp_url = shp_url
            model.shx_url = shx_url
            model.put()
            return model
        else:
            return False
        


if __name__ == '__main__':
    shp = open('../../../../../../example_data/stl_hom/stl_hom.shp','rb').read()
    shx = open('../../../../../../example_data/stl_hom/stl_hom.shx','rb').read()
    model = new_shapefile(shp,shx)

