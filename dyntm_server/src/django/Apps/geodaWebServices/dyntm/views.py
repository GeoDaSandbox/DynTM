# Built-in Imports
import logging
import zlib, base64
import hashlib
import array
UNSIGNED_ITEM_TYPES = {array.array('B').itemsize:'B', array.array('H').itemsize:'H', array.array('I').itemsize:'I', array.array('L').itemsize:'L'}
import os
import time
from cStringIO import StringIO
# Django Imports
from django.template import Template
# Custom Imports
from geodaWebServices import WebService
from gws_lib import db
from gws_lib import memcache
from geodaWebServices.shapeManager.models import Shapefile,new_shapefile,new_shapefile_from_parts,upload_part_of_shapefile,complete_multipart_upload
# Local Imports
from models import TileSet,Tile,Classification,ColorScheme
# DynTM Imports
from render import render,classification,colors,query

MAX_n = 256 #254 regions + Background + Borders

logging.basicConfig(filename='/var/log/dtm.log',level=logging.INFO)
logger = logging.getLogger("gws.dtm")
#logging.debug('This message should go to the log file')

class DTMHandler(WebService):
    def __init__(self,format='HTML',auth=True):
        t = Template("<html><head><title>DynTM</title></head><body>{{body}}</body></html>")
        WebService.__init__(self,format,t,auth_required=auth)
    def call(self,*args,**kwargs):
        self.reset()
        return WebService.call(self,*args,**kwargs)
    def reset(self):
        self.tsid = None
        self._ts = None
        self.tid = None
        self._tile = None
        self.clid = None
        self._cl = None
        self.csid = None
        self._cs = None
        self._get_raw = False
    @property
    def cs(self):
        if self._cs:
            return self._cs
        if self.csid:
            csid = self.csid
        else:
            csName = self.request.REQUEST.get('cs')
            if csName:
                self.csid = csid = csName
            else:
                return False
        cs = memcache.get(csid.encode('utf8'))
        if cs is None:
            cs = ColorScheme.get_by_key_name(csid)
            if cs:
                cs.alphas = '\x00'
                if not memcache.add(csid.encode('utf8'), cs):
                    logger.error("Memcache set failed [ %s ]"%csid)
                self._cs = cs
        #logger.info(self._cs)
        if cs is not None:
            if cs.public or cs.owner == self.request.user.username:
                self._cs = cs
                return self._cs
        return False
    @property
    def cl(self):
        if self._cl:
            return self._cl
        if self.clid:
            clid = self.clid
        else:
            clName = self.request.REQUEST.get('cl')
            if clName:
                self.clid = clid = clName
            else:
                return False
        cl = memcache.get(clid.encode('utf8'))
        if cl is None:
            if clid.isdigit() and len(clid)<4:
                logger.warn("User requested a random classification, not fully implemented")
                cl = classification.random(self.ts.numregions,min(int(clid)+2,MAX_n))
                self._cl = cl
                return cl
            else:
                cl = Classification.get_by_key_name(clid)
                if cl is not None and not memcache.add(clid.encode('utf8'), cl):
                    logger.error("Memcache set failed [ %s ]"%clid)
        if cl is not None:
            if cl.public or cl.owner == self.request.user.username:
                self._cl = cl
                return self._cl
        return False
    @property
    def ts(self):
        """ Search for the TileSetName in the Request and try and load it from Memcache or DataStore, return TileSet or False """
        if self._ts:
            return self._ts
        if self.tsid:
            tsid = self.tsid
        else:
            tileSetName = self.request.REQUEST.get('ts')
            if tileSetName:
                self.tsid = tsid = tileSetName
            else:
                return False
        ts = memcache.get(tsid.encode('utf8'))
        if ts is None:
            ts = TileSet.get_by_key_name(tsid)
            if ts is not None and not memcache.set(tsid.encode('utf8'),ts):
                logger.error("Memcache set failed [ %s ]"%tsid)
        if ts is not None:
            if ts.public or ts.owner == self.request.user.username:
                self._ts = ts
                return ts
        return False
    @property
    def tile(self):
        if self._tile and not self._get_raw:
            return self._tile
        if not self.ts:
            return False
        get = self.request.REQUEST.get
        x = get('x')
        y = get('y')
        z = get('z')
        b = True
        if get('b',-1) == '0':
            b = False
        if not (x and y and z):
            return False
        try:
            z,x,y = map(int,[z,x,y])
            if self._get_raw:
                shpfile = Shapefile.get_by_key_name(self.ts.shpfile)
                png = shpfile.raw_png(x,y,z,border=b)
                return png
            if b:
                tid = "t:%s:%d+%d+%d"%(self.ts.shpfile,z,x,y)
            else:
                tid = "u:%s:%d+%d+%d"%(self.ts.shpfile,z,x,y)
            tile = Tile.get_by_key_name(tid)
            if tile:
                self._tile = tile
                return tile
            else:
                logger.info("Creating tile x%d,y%d,z%d of %s"%(x,y,z,tid))
                shpfile = memcache.get(self.ts.shpfile.encode('utf8'))
                if not shpfile:
                    shpfile = Shapefile.get_by_key_name(self.ts.shpfile)
                    memcache.set(self.ts.shpfile.encode('utf8'),shpfile)
                typ,dat = shpfile.raw_tile(x,y,z,border=b)
                tile = Tile(tid)
                tile.typ = typ
                tile.dat = str(dat)
                tile.put()
                self._tile = tile
                return tile
        except:
            logger.error("Exception occured while Getting or Creating Tile (x%d,y%d,z%d)"%(x,y,z))
            return False
        return False

class TileHandler(DTMHandler):
    def __init__(self,format='png',auth=False):
        DTMHandler.__init__(self,format,auth)
    def get(self):
        ts = self.ts
        tile = self.tile
        cl = self.cl
        if ts and tile:
            #if cl:
            #    #png = render.overview(ts.n,tile.typ,tile.dat,C=classification.Classification(cl.a))
            #    png = render.overview(ts.numregions,tile.typ,tile.dat,C=cl)
            #else:
            png = render.overview(ts.numregions,tile.typ,tile.dat,C=self.cl,CS=self.cs)
            return self.write(png)
        else:
            return self.error(404)
        return self.write("Got Here")
class RawTileHandler(DTMHandler):
    def __init__(self,format='png',auth=False):
        DTMHandler.__init__(self,format,auth)
    def get(self):
        ts = self.ts
        self._get_raw = True
        png = self.tile
        if ts and png:
            return self.write(png)
        else:
            return self.error(404)
        return self.write("Got Here")
class TileSetHandler(DTMHandler):
    def __init__(self,format='json'):
        DTMHandler.__init__(self,format,auth=set(['POST','DELETE']))
        #self.change_permission('GET',False)
    def get(self,tsid=''):
        if tsid:
            self.tsid = tsid
            ts = self.ts
            if ts:
                if self.request.GET.get('type',None) == 'polys':
                    zoom = int(self.request.GET.get('z',0))
                    shpfile = Shapefile.get_by_key_name(self.ts.shpfile)
                    return self.write(shpfile.polygons(zoom),remove_white_space=True)
                return self.write(ts.as_dict())
            else:
                return self.write({"error":"TileSet Not Found"})
        else:
            return self.write({'tilesets':TileSet.select('owner',self.request.user.username,keys_only=True)})
    def post(self,tsid=''):
        if self.request.user.is_authenticated():
            user = self.request.user
            logger.info("%s, is creating a new TileSet."%(user.username))
            POST = self.request.POST
            # SINGLE PART UPLOAD, CREATE NEW SHAPEFILE
            if 'shp' in POST and 'shx' in POST:
                shp = zlib.decompress(base64.b64decode(POST['shp']))
                shx = zlib.decompress(base64.b64decode(POST['shx']))
                #dbf = zlib.decompress(base64.b64decode(POST['dbf']))
                shapeModel = new_shapefile(shp,shx)
                ts = TileSet("%s:%s"%(user.username,shapeModel.key_name))
                ts.owner = user.username
                ts.public = True
                ts.date = time.mktime(time.gmtime())
                ts.numregions = shapeModel.n
                ts.shpfile = shapeModel.key_name
                return self.write({'TileSetID':ts.put()})
            # MULTIPART UPLOAD: Initiate Upload
            elif 'shpmd5' in POST and 'shx' in POST:
                shpmd5 = POST['shpmd5'].upper()
                if TileSet.get_by_key_name('%s:%s'%(user.username,shpmd5)):
                    return self.write({'TileSetID':'%s:%s'%(user.username,shpmd5)})
                shapeModel = Shapefile.get_by_key_name(shpmd5)
                if shapeModel:
                    ts = TileSet("%s:%s"%(user.username,shapeModel.key_name))
                    ts.owner = user.username
                    ts.public = True
                    ts.date = time.mktime(time.gmtime())
                    ts.numregions = shapeModel.n
                    ts.shpfile = shapeModel.key_name
                    return self.write({'TileSetID':ts.put()})
                else: #need to upload data.
                    shx = zlib.decompress(base64.b64decode(POST['shx']))
                    uploadID = new_shapefile_from_parts(shpmd5,shx)
                    if uploadID:
                        return self.write({"uploadId":uploadID})
                    else:
                        return self.write({'error':"Could not initiate multipart upload. Uknown error."})
            # MULTIPART UPLOAD: Upload Part
            elif 'shpmd5' in POST and 'uploadId' in POST and 'partNum' in POST and 'shpPart' in POST:
                shpPart = zlib.decompress(base64.b64decode(POST['shpPart']))
                etag = upload_part_of_shapefile(POST['shpmd5'],POST['uploadId'],int(POST['partNum']),shpPart)
                if etag:
                    return self.write({"etag":etag})
                else:
                    return self.write({'error':"Could not upload part. Try Again."})
            # MULTIPART UPLOAD: Complete Upload.
            elif 'shpmd5' in POST and 'uploadId' in POST and 'partsList' in POST:
                parts = {}
                for i,etag in enumerate(POST['partsList'].split(',')):
                    parts[i+1] = etag
                shapeModel = complete_multipart_upload(POST['shpmd5'],POST['uploadId'],parts)
                ts = TileSet("%s:%s"%(user.username,shapeModel.key_name))
                ts.owner = user.username
                ts.public = True
                ts.date = time.mktime(time.gmtime())
                ts.numregions = shapeModel.n
                ts.shpfile = shapeModel.key_name
                return self.write({'TileSetID':ts.put()})
            return self.write({'error':"Missing required arguments 'shp' and/or 'shx'."})
        else:
            return self.write({'error':"User not authenticated."})
        return self.write({'error':"An unknown error occured."})
    def delete(self,tsid=''):
        if tsid:
            self.tsid = tsid
            ts = self.ts
            if ts and ts.owner == self.request.user.username:
                ts.delete()
                memcache.delete(tsid.encode('utf8'))
                return self.write(True)
            else:
                return self.write({"error":"TileSet Not Found"})
        return self.write({'msg':"Error: Missing TileSet"})
class ClassificationHandler(DTMHandler):
    def __init__(self,format='json'):
        DTMHandler.__init__(self,format,auth=set(['GET','POST','DELETE']))
        #DTMHandler.__init__(self,format,auth=set([]))
    def delete(self,clid=''):
        if clid:
            self.clid = clid
            cl = self.cl
            if cl and cl.owner == self.request.user.username:
                cl.delete()
                memcache.delete(clid.encode('utf8'))
                return self.write(True)
            else:
                return self.write({"error":"Classification Not Found"})
        return self.write({"error":"Missing Classification ID"})
    def get(self,clid=''):
        if clid:
            self.clid = clid
            cl = self.cl
            if cl:
                dat = cl.as_dict()
                out = {}
                for key,val in dat.iteritems():
                    try:
                        if issubclass(type(val),basestring):
                            out[key] = val.encode('utf8')
                        else:
                            out[key] = val
                    except UnicodeDecodeError: pass
                return self.write(out)
            else:
                return self.write({"error":"Classification Not Found"})
        else:
            return self.write({'classifications':Classification.select('owner',self.request.user.username,keys_only=True)})
    def post_b64zlib(self,bg=0,br=1):
        user = self.request.user
        POST = self.request.POST
        if 'dat' in POST:
            dat = zlib.decompress(base64.b64decode(POST['dat']))
            a = array.array(UNSIGNED_ITEM_TYPES[1])
            a.fromlist([bg,br])
            a.fromstring(dat)
            astring = a.tostring()
            cl = Classification("%s:%s"%(user.username,hashlib.md5(astring).hexdigest()))
            cl.tileset = self.ts.key_name
            cl.dat = zlib.compress(astring)
            cl.N = len(a)
            assert (cl.N-2) == self.ts.numregions
            cl.n = max(a)+1
            cl.owner = user.username
            cl.public = True
            cl.expires = False
            cl.date = time.mktime(time.gmtime())
            return cl.put()
    def post_csv(self,bg=0,br=1):
        user = self.request.user
        POST = self.request.POST
        if 'dat' in POST:
            a = array.array(UNSIGNED_ITEM_TYPES[1])
            dat = map(int,POST['dat'].split(','))
            a.fromlist([bg,br])
            a.fromlist(dat)
            astring = a.tostring()
            cl = Classification("%s:%s"%(user.username,hashlib.md5(astring).hexdigest()))
            cl.tileset = self.ts.key_name
            cl.dat = zlib.compress(astring)
            cl.N = len(a)
            assert (cl.N-2) == self.ts.numregions
            cl.n = max(a)+1
            cl.owner = user.username
            cl.public = True
            cl.expires = False
            cl.date = time.mktime(time.gmtime())
            return cl.put()
    def post(self,clid=''):
        format = {'b64zlib':self.post_b64zlib, 'csv':self.post_csv}
        bgclass = 0
        brclass = 1
        if self.request.user.is_authenticated():
            user = self.request.user
            logger.info("%s, is creating a new Classification."%(user.username))
            POST = self.request.POST
            if 'format' in POST and 'tsid' in POST:
                self.tsid = POST['tsid']
                if not self.ts:
                    return self.write({'error':"Invalid TileSet"})
                if not POST['format'].lower() in format:
                    return self.write({'error':"Invalid format."})
                if 'background' in POST and POST['background'].isdigit():
                    bgclass = int(POST['background'])
                if 'borders' in POST and POST['borders'].isdigit():
                    brclass = int(POST['borders'])
                try:
                    clid = format[POST['format']](bg=bgclass,br=brclass)
                    return self.write({'ClassificationID':clid})
                except:
                    raise
                    #pass
        return self.write({"error":"Classification not created"})
class ColorSchemeHandler(DTMHandler):
    def __init__(self,format='json'):
        DTMHandler.__init__(self,format,auth=set(['GET','POST','DELETE']))
    def delete(self,csid=''):
        if csid:
            self.csid = csid
            cs = self.cs
            if cs and cs.owner==self.request.user.username:
                cs.delete()
                memcache.delete(csid.encode('utf8'))
                return self.write(True)
            else:
                return self.write({"error":"Color Scheme Not Found"})
        return self.write({"error":"Missing Color Scheme ID"})
    def get(self,csid=''):
        if csid:
            self.csid = csid
            cs = self.cs
            if cs:
                dat = cs.as_dict()
                out = {}
                for key,val in dat.iteritems():
                    try:
                        if issubclass(type(val),basestring):
                            out[key] = val.encode('utf8')
                    except UnicodeDecodeError: pass
                out['colors'] = ['#'+''.join(['%0.2X'%ord(y) for y in x]) for x in dat['colors']]
                if 'alphas' in dat:
                    out['alphas'] = map(ord,dat['alphas'])
                return self.write(out)
            else:
                return self.write({"error":"ColorScheme Not Found"})
        else:
            POST = self.request.POST
            if 'numclasses' in POST and POST['numclasses'].isdigit():
                return self.write({'colorschemes':ColorScheme.select('n',POST['numclasses'],keys_only=True)})
            return self.write({'colorschemes':ColorScheme.select('owner',self.request.user.username,keys_only=True)})
    def post(self,csid=''):
        bgcolor = '#000001'
        brcolor = '#000000'
        if self.request.user.is_authenticated():
            user = self.request.user
            logger.info("%s, is creating a new ColorScheme."%(user.username))
            POST = self.request.POST
            if 'colors' in POST:
                if 'background' in POST:
                    bgcolor = POST['background']
                if 'borders' in POST:
                    brcolor = POST['borders']
                colors = [bgcolor,brcolor]+POST['colors'].encode('utf8').split(',')
                color_list = []
                for color in colors:
                    if color[0] == '#':
                        color = color[1:]
                    r,g,b = [color[x:x+2] for x in range(0,6,2)]
                    col = ''.join(map(chr,[int(r,16),int(g,16),int(b,16)]))
                    color_list.append(col)
                cs = ColorScheme("%s:%s"%(user.username,hashlib.md5(''.join(color_list)).hexdigest()))
                cs.n = len(color_list)
                cs.colors = color_list
                if 'alphas' in POST:
                    logger.warn("User: %s, tried to post a color scheme with Alphas, not supported yet"%user.username)
                cs.owner = user.username
                cs.public = True
                cs.expires = False
                cs.date = time.mktime(time.gmtime())
                return self.write({"ColorSchemeID":cs.put()})
