# Built-in Imports
import zlib
import array
import logging
from math import ceil,floor
from base64 import b64decode
from time import time
# Django Imports
from django.http import HttpResponse,HttpResponseRedirect
from django.template import Template
from django.core.exceptions import ObjectDoesNotExist
#from django.conf import settings
# Custom Imports
from geodaWebServices import WebService
from geodaWebServices.lib import db
from geodaWebServices.lib import memcache
# DynTM Imports
from render import render,classification,colors,query
# Local Imports
from models import TileSet,Tile,Classification,ColorScheme,Overview,TileSet_IDS
# Imports that need to go away
from cStringIO import StringIO
import os.path
#from google.appengine.ext import webapp
#from google.appengine.ext.webapp import template

UNSIGNED_ITEM_TYPES = {array.array('B').itemsize:'B', array.array('H').itemsize:'H', array.array('I').itemsize:'I', array.array('L').itemsize:'L'}
logging.basicConfig(filename='/var/tmp/dtm/dtm.log',level=logging.DEBUG)
logging.debug('This message should go to the log file')
MAX_n = 256 #254 regions + Background + Borders
MAX_N = 254
LOCAL_GMAP_KEY = 'ABQIAAAAPih0F8hZWxspOwpW0boEJBT2yXp_ZAY8_ufC3CFXhHIE1NvwkxRk1j9aES-drlfa1zM9tIglPJFFUQ'
DWMS_GMAP_KEY = 'ABQIAAAAPih0F8hZWxspOwpW0boEJBQdApxSCAkbaHWRuz9a4sLR7k5V-xTbEpXdKkMw3zKTGARvHKKd4Iwrrw'
WATERSIM_GMAP_KEY = 'ABQIAAAAPih0F8hZWxspOwpW0boEJBQmNczTuLosm9TaoRidQYZU2tEm_hTYX4j2rcYb_MAgIz01edFcWYUR7w'
GEODAMAPS_GMAP_KEY = 'ABQIAAAAq6q1Bfz2M-4BvjbnboenOhSluERgOAIQmKdxstqa-SNVEsOUXRQsOX2zAiIrlYe1P8pewy-byt11Vw'
TILE_LIFE_SPAN = "max-age=300" # 5 * 60seconds
#/ Since tiles of different classifcations have different URL's they could live forever.
PREFIX = ''

class DTMHandler(WebService):
    def __init__(self,format='HTML'):
        t = Template("<html><head><title>DynTM</title></head><body>{{body}}</body></html>")
        WebService.__init__(self,format,t,auth_required=False)
    def get(self,*args,**kwargs):
        self._ts = None
        self.tsid = None
        self._cl = None
        self._cs = None
        self._tile = None
        return self.real_get(*args,**kwargs)
    def post(self):
        self._ts = None
        self.tsid = None
        self._cl = None
        self._cs = None
        self._tile = None
        return self.real_post()
    def real_get(self):
        return self.write({'body':"<center>Welcome to dynTM...<br><br>...More coming soon!</center>"})
    
    @property
    def ts(self):
        """ Search for the TileSetName in the Request and try and load it from Memcache or DataStore, return True or False """
        if self._ts:
            return self._ts
        if self.tsid:
            tsid = self.tsid
        else:
            tileSetName = self.request.REQUEST.get('ts')
            if tileSetName:
                self.tsid = tsid = 'ts:'+tileSetName
            else:
                return False
        ts = memcache.get(tsid)
        if ts is not None:
            self._ts = ts
        else:
            ts = TileSet.get_by_key_name(tsid)
            #if ts is not None and not memcache.add(tsid, ts):
            #    logging.error("Memcache set failed [ %s ]"%tsid)
            self._ts = ts
        #logging.info(self._ts)
        if ts is not None:
            return self._ts
        else:
            return False
    @property
    def cl(self):
        """ Search for the Classification Name in the Request and try and load it from Memcache or DataStore, return True or False """
        if self._cl:
            return self._cl
        classificationName = self.request.REQUEST.get('cl','DEFAULT')
        if classificationName == 'random':
            self.clid = clid = "cl:random"
        elif classificationName.isdigit():
            self.clid = clid = "cl:__digit:"+self.ts.name+":"+classificationName
        elif self.ts:
            self.clid = clid = "cl:"+self.ts.name+":"+classificationName
        else:
            return False
        cl = memcache.get(clid)
        if cl is not None:
            self._cl = cl
        else:
            cl = None
            if self.ts:
                N = self.ts.idlen
                if clid == 'cl:random':
                    cl = classification.random(N,min(N,MAX_n))
                elif clid.startswith('cl:__digit:'):
                    cl = classification.random(N,min(int(classificationName)+2,MAX_n))
                elif clid.startswith('cl:key_'):
                    C = Classification.get(classificationName[4:])
                    if C:
                        cl = classification.Classification(C.a)
                elif clid:
                    C = Classification.get_by_key_name(clid)
                    if C:
                        cl = classification.Classification(C.a)
                #if cl and clid != 'cl:random':
                    #if not memcache.add(clid, cl, 60):
                    #    logging.error("Memcache set failed [ %s ]"%clid)
                if not cl:
                    cl = classification.random(N,3)
            self._cl = cl
        if cl is not None:
            return cl
        else:
            return False
    @property
    def cs(self):
        """ Search for the Color Scheme Name in the Request and try and load it from Memcache or DataStore, return True or False """
        if self._cs:
            return self._cs
        colorSchemeName = self.request.REQUEST.get('cs','DEFAULT')
        self.csid = csid = "cs:"+colorSchemeName
        cs = memcache.get(csid)
        if cs is not None:
            self._cs = cs
        else:
            if csid:
                cs = ColorScheme.get_by_key_name(csid)
                if cs:
                    #logging.info('found colorScheme(%s)'%csid)
                    #CHECK URL FOR BANGGROUND OPTIONS...
                    background = self.request.REQUEST.get('transparentBackground')
                    if background == 'OFF':
                        cs.alphas = ''
                    self._cs = cs
            if self.cl:
                if cs and cs.n==self.cl.n:
                    pass
                else:
                    N = min(self.cl.n-2,MAX_N)
                    if csid[:9] == 'cs:random':
                        rid = 'ts:%s&cl:%s&cs:%s'%(self.request.REQUEST.get('ts'),self.request.REQUEST.get('cl'),self.request.REQUEST.get('cs'))
                        cs = memcache.get(rid)
                        if not cs:
                            cs = colors.random(N,borders=(60,60,60))
                            memcache.add(rid, cs)
                        self._cs = cs
                        return cs
                    else:
                        if self.cl.n == 3:
                            cs = colors.ColorScheme([(0,0,1),(0,0,0)]+[(255,90,0)]*N)
                        else:
                            cs = colors.fade(self.cl.n-2)
            self._cs = cs
        if cs is not None:
            return cs
        else:
            return False
    @property
    def tile(self):
        #logging.info('in tile prop')
        if self._tile:
            return self._tile
        if not self.ts:
            return False
        g = self.request.REQUEST.get
        z,x,y = map(g,'zxy')
        return self.find_tile(z,x,y)
    def find_tile(self,z,x,y):
        if z is not None and x is not None and y is not None and self.ts:
            z,x,y = map(int,(z,x,y))
            #logging.info('Find Tile: %d+%d+%d'%(z,x,y))
            if self.get_tile(z,x,y):
                return self._tile
            elif self.valid_tile(z,x,y):
                #logging.info('Tile: %d+%d+%d Not Found, will search'%(z,x,y))
                while z:
                    z-=1
                    x_quad = x&1
                    y_quad = y&1
                    x = x>>1
                    y = y>>1
                    #logging.info('Tile: search %d+%d+%d'%(z,x,y))
                    if self.get_tile(z,x,y):
                        #logging.info('Tile: found %d+%d+%d'%(z,x,y))
                        regionID = query.query(self._tile,qx=x_quad,qy=y_quad)
                        #logging.info('Region ID: %d'%(regionID))
                        #logging.info('Quad x,y: (%d,%d)'%(x_quad,y_quad))
                        t = Tile()
                        t.dat = str(regionID)
                        if regionID == 0:
                            t.typ = 'A'
                        else:
                            t.typ = 'B'
                        self._tile = t
                        return self._tile
            else:
                #logging.info('Tile: %d+%d+%d Is Not Valid'%(z,x,y))
                return False
        else:
            #logging.info('not z,x,y or ts')
            t =Tile()
            t.dat = '0'
            t.typ = 'A'
            self._tile = t
            return self._tile
        return False
    def get_tile(self,z,x,y):
        tid = "t:%s:%d+%d+%d"%(self.ts.name,z,x,y)
        tile = memcache.get(tid)
        if tile is not None:
            self._tile = tile
            return True
        tile = Tile.get_by_key_name(tid)
        if tile:
            #if tile.typ == 'B':
            #    tile.delete()
            #    return False
            #if not memcache.add(tid, tile):
            #    logging.error("Memcache set failed [ %s ]"%tid)
            self._tile = tile
            return True
        return False
    def valid_tile(self,z,x,y):
        """ Checks is X and Y are within the max allowable bounds for a particular zoom level
            Does not take into account a particular tileSet, but it could
        """
        #logging.info('Check Valid Tile: %d+%d+%d'%(z,x,y))
        maxIndex = 2**z-1
        #logging.info('maxIndex: %d'%maxIndex)
        #logging.info('maxZoom: %d'%self.ts.maxZoom)
        if x>maxIndex or y>maxIndex:
            return False
        if z > self.ts.maxZoom:
            return False
        return True

        
    def die(self,e):
        self.response.clear()
        return self.error(e)
class TileSetHandler(DTMHandler):
    def __init__(self,format='HTML'):
        DTMHandler.__init__(self,format)
        if format.lower() == 'html':
            self.template = Template("""<html><head><title>DynTM</title></head><body>The following public datasets are available:<br>
{% for ts in public %}
<li>{{ ts }}</li>
{% endfor %}
</body></html>""")
    def real_get(self,tsid=''):
        if tsid:
            if tsid.startswith('ts:'):
                self.tsid = tsid
            else:
                self.tsid = 'ts:'+tsid
            ts = self.ts
            if ts:
                return self.write(ts.as_dict())
            else:
                return self.write({"error":"TileSet Not Found"})
        else:
            return self.write({'public':[ts for ts in TileSet.all(keys_only=True)]})
class TileSetIdsHandler(DTMHandler):
    def real_get(self):
        ts = self.ts
        if self.ts:
            ids = ts.ids.ids
            if issubclass(type(ids),basestring):
                ids = TileSet_IDS.get_by_key_name(ids)
            ids = zlib.decompress(ids)
            ids = ids.split(',')
            self.response.headers["Content-Type"] = "text/csv"
            self.write('RegionID,Value\n')
            self.write(''.join(['"%s",\n'%i for i in ids]))
            
class OverviewHandler(DTMHandler):
    def real_get(self):
        ts = self.ts
        if ts:
            o = ts.overview
            if issubclass(type(o),basestring):
                o = Overview.get_by_key_name(o)
            png = render.overview(ts.idlen, o.typ, o.dat, o.width, o.height, CS=self.cs, C=self.cl)
            self.response.headers["Content-Type"] = "image/png"
            self.response.out.write(png)
class ClassifyHandler(DTMHandler):
    """ClassifyHandler: Provides a basic API for Classifing a TileSet.
    """
    def real_get(self):
        """ Handles /classify GET requests.
            A basic request with return a form setup for posting a new Classification.
            
            append '?noform=1' to the GET request and we return a comma seperated list of ID's
            The list of ClassIds sent in to the POST handler need to be in this order.
        """
        if self.ts:
            ts = self.ts
            noform = self.request.REQUEST.get('noform')
            if noform:
                self.response.headers["Content-Type"] = "text/txt"
                ids = ts.ids
                if issubclass(type(ids),basestring):
                    ids = TileSet_IDS.get_by_key_name(ids)
                ids = zlib.decompress(ids.ids)
                if noform=='json':
                    json = '{"ids":"%s"}'%ids
                    callback = self.request.REQUEST.get('callback')
                    if callback:
                        json = "%s(%s)"%(callback,json)
                    return self.write(json)
                self.write(ids)
            else:
                tpath = os.path.join(os.path.dirname(__file__), 'templates/classify.html')
                self.write(template.render(tpath, {'ts_name':ts.name}))
                #form = '<html><body><form action="/classify/" method="post">'
                #form+= '<INPUT type="hidden" name="ts" id="ts" value="%s">'%ts.name
                #form+= 'Name: <INPUT type="text" name="name" id="name" value="MOIL">'
                #form+= '<LABEL for="classification">Classification = 0,1,</LABEL><BR>'
                #form+= '<TEXTAREA rows="6" cols="100" name="classification" id="classification"></TEXTAREA><BR>'
                #form+= '<INPUT type="submit" value="Send">'
                #form+= '</form></body></html>'
                #self.write(form)
    def real_post(self):
        """ Handles /classify POST requests/
            The POST data must contain "classifcation" and "ts"
            'classification': a string of integers in the range >=2 and <=255.
                                0 and 1 are reserved for background and borders
                                each integer represents the classID of a region,
                                the order of the class ids MUST match the order
                                of the IDS provided by the GET ?noform=1 handler.
        """
        if self.ts:
            cl = self.request.REQUEST.get('classification')
            b64 = self.request.REQUEST.get('b64encode')
            if not cl:
                self.write("Bad Request")
                return self.die(400)
            try:
                if b64 == 'True':
                    a = array.array('B')
                    a.fromstring(b64decode(cl))
                    cl = a.tolist()
                else:
                    cl = cl.strip().split(',')
                    cl = map(int,cl)
                assert len(cl) == self.ts.idlen
                cl = [0,1]+cl
                a = array.array(UNSIGNED_ITEM_TYPES[1])
                a.fromlist(cl)
                a = zlib.compress(a.tostring())
                name = self.request.REQUEST.get('name')
                exp = False
                if not name:
                    name = 'user_%s'%str(time()).replace('.','')
                    exp = True
                if name:
                    clid = 'cl:%s:%s'%(self.ts.name,name)
                    memcache.delete(clid)
                    C = Classification(key_name=clid)
                    C.name = name
                    C.expires = exp
                #else:
                #    key_name = 'cs:%s:%s'%(self.ts.name,str(time()).replace('.',''))
                #    C = Classification(key_name)
                C.tileset = self.ts.key()
                C.a = a
                C.N = len(cl)-2
                C.n = max(cl)+1
                title = self.request.REQUEST.get('title')
                if title:
                    C.title = title
                notes = self.request.REQUEST.get('notes')
                if notes:
                    C.notes = notes
                public = self.request.REQUEST.get('public')
                if public and public == 'False':
                    C.public = False
                elif public:
                    C.public = True
                try:
                    key = C.put()
                except CapabilityDisabledError:
                    logging.error("Capability has been disabled")
                    self.dir(500)
                callback = self.request.REQUEST.get("callback")
                if name:
                    if callback:
                        self.write('%s({"key":"%s"})'%(callback,name))
                    else:
                        self.write("Put: %s"%name)
                else:
                    if callback:
                        self.write('%s({"key":"%s"})'%(callback,key))
                    else:
                        self.write("Put: key_%s"%key)
            except:
                raise 
        else:
            self.die(400)
            
class LegendHandler(DTMHandler):
    def real_get(self):
        values = self.request.REQUEST.get('values')
        if not values and self.cl:
            C = Classification.get_by_key_name(self.clid)
            if C and hasattr(C,'notes'):
                values = C.notes
            else:
                values = ','.join(map(str,range(self.cl.n)))
        if self.cs and values:
            delim = self.request.REQUEST.get('delim')
            if not delim: delim = ','
            title = self.request.REQUEST.get('title')
            values = values.split(delim)
            s = '<div style="width:170px; background-color:#cccccc; padding:5px;">'
            if title: s+='<h3 style="margin:0;border:0;padding:0;">%s</h3>'%title
            #for i in range(2,self.cs.n):
            for i,val in enumerate(values):
                r,g,b = map(ord,self.cs.colors[i+2])
                s += '<div style="clear:both; float:left; border: 1px black solid; width:20px; height:20px; background-color:#%.2X%.2X%.2X;"> </div>'%(r,g,b)
                #s += '<div style="height:22px;">'+values[i-2]+'</div>'
                s += '<div style="height:22px;">'+val+'</div>'
            s += '</div>'
            callback = self.request.REQUEST.get('callback')
            if callback:
                s = callback+'({"legend":"%s"})'%s.replace('"','\\"')
            self.write(s)
            
class ColorSchemeHandler(DTMHandler):
    """ColorSchemeHandler: Provides a basic API for add Color Schemes
    """
    def real_get(self):
        """ Handles /classify GET requests.
            A basic request with return a form setup for posting a new ColorScheme
        """
        callback = self.request.REQUEST.get("callback")
        if callback:
            json = callback+'({"colors":['
        else:
            self.write('<html><body>')
            self.write('<table><tr><th>ColorName</th><th>n</th><th>Colors</th></tr>')
        q = ColorScheme.all(keys_only=True)
        n = self.request.REQUEST.get('n')
        if n:
            q.filter("n",int(n)+2)
        #class fake_cl:
        #    a = range(20)
        #fake_cl = fake_cl()
        for key in q:
            c = ColorScheme.get(key)
            s = '<div>'
            for i in range(2,c.n):
                r,g,b = map(ord,c.colors[i])
                s += '<div style="float:left; border: 1px black solid; width:20px; height:20px; background-color:#%.2X%.2X%.2X;"> </div>'%(r,g,b)
            s += '</div>'
            if callback:
                json += '{"name":"%s","sample":\'%s\'},'%(c.name,s)
            else:
                row = '<tr><td>%s</td><td>%d</td><td>%s</td></tr>'%(c.name,c.n-2,s)
                self.write(row)
        if callback:
            json = json[:-1]+"]})"
            self.write(json)
    def send_form(self):
        form = '<form action="/colors/" method="post">'
        form+= '<LABEL for="colors">Colors</LABEL><BR>'
        form+= '<TEXTAREA rows="6" cols="100" name="colors" id="colors" >#000001,#000000,</TEXTAREA><BR>'
        #form+= '<LABEL for="alphas">Alpha Values</LABEL><BR>'
        #form+= '<TEXTAREA rows="3" cols="100" name="alphas" id="alphas" >0,255,</TEXTAREA><BR>'
        form+= 'Color Scheme Name: <INPUT type="text" id="name" name="name"><BR>'
        form+= '<INPUT type="submit" value="Send">'
        form+= '</form></body></html>'
        self.write(form)
    def real_post(self):
        colors = self.request.REQUEST.get('colors')
        name = self.request.REQUEST.get('name')
        if colors and name:
            colors = colors.encode('utf8')
            color_list = []
            for color in colors.split(','):
                if color[0] == '#':
                    color = color [1:]
                r,g,b = [color[x:x+2] for x in range(0,6,2)]
                col = ''.join(map(chr,[int(r,16),int(g,16),int(b,16)]))
                color_list.append(db.ByteString(col))
            c = ColorScheme(key_name='cs:%s'%name)
            c.name = name
            c.n = len(color_list)
            c.colors = color_list
            alphas = self.request.REQUEST.get('alphas')
            if alphas:
                if alphas == "0,255,":
                    pass
                else:
                    values = map(int,alphas.split(','))
                    c.alphas = ''.join(map(chr,values))
            try:
                key = c.put()
            except CapabilityDisabledError:
                logging.error("Capability has been disabled")
                self.dir(500)
            self.write(key)
        else:
            self.write("bad request")
        
        

class GMapHandler(DTMHandler):
    def real_get(self):
        if not self.ts:
            return self.die(404)
        values = {'host_url':self.request.host_url,'tileSet':self.ts.name,'classification':1,'colorScheme':''}
        values['cLat'] = self.ts.cLat
        values['cLng'] = self.ts.cLng
        values['minx'] = self.ts.minx
        values['miny'] = self.ts.miny
        values['maxx'] = self.ts.maxx
        values['maxy'] = self.ts.maxy
        background = self.request.REQUEST.get('transparentBackground')
        if background == 'OFF':
            values['background'] = '&transparentBackground=OFF'
        else:
            values['background'] = ''
        b = self.ts.GMERC_BOUNDS
        extents = []
        for z in range(self.ts.maxZoom+1):
            extents.append(gTileBounds(b,z)[:-1])
        values['extents'] = str(extents)
        values['maxZoom'] = self.ts.maxZoom

        cs_name = self.request.REQUEST.get('cs')
        if cs_name:
            values['colorScheme'] = cs_name
        cl_name = self.request.REQUEST.get('cl')
        if cl_name:
            values['classification'] = cl_name
        host = self.request.host.lower()
        if 'localhost' in host:
            values['API_KEY'] = LOCAL_GMAP_KEY
        if 'dwms' in host:
            values['API_KEY'] = DWMS_GMAP_KEY
        if 'watersim' in host:
            values['API_KEY'] = WATERSIM_GMAP_KEY
        if 'geodamaps' in host:
            values['API_KEY'] = GEODAMAPS_GMAP_KEY
        map_templates = {
                'simple':'templates/gmap_simple.html',
                'hybrid':'templates/gmap_hybrid.html',
                'transparent':'templates/gmap_transparent.html',
                'embed':'templates/gmap_transparent_embed.html',
                'embed2':'templates/gmap_transparent_embed2.html',
                'ol':'templates/openlayers.html'}
        mtp = self.request.REQUEST.get('template')
        if mtp in map_templates:
            template_file = map_templates[mtp]
        else:
            template_file = map_templates['transparent']
        tpath = os.path.join(os.path.dirname(__file__), template_file)
        self.response.out.write(template.render(tpath, values))
            
class TileHandler(DTMHandler):
    def real_get(self):
        ts = self.ts
        tile = self.tile
        if ts and tile:
            png = render.overview(ts.idlen, tile.typ, tile.dat, CS=self.cs, C=self.cl)
            self.response.headers["Content-Type"] = "image/png"
            self.response.headers["Cache-Control"] = TILE_LIFE_SPAN
            self.response.out.write(png)
        else:
            #logging.info('no tile or ts')
            #logging.info(tile)
            #logging.info(ts)
            return self.die(404)

class QueryHandler(DTMHandler):
    def real_get(self):
        if not self.ts:
            return self.die(500)
        try:
            x,y = self.request.REQUEST.get('pixelxy').split(',')
            x,y = int(x),int(y)
            z = int(self.request.REQUEST.get('zoom').split(',')[0])
            tx,ty = x/256,y/256
            ox,oy = x%256,y%256
            tile = self.find_tile(z,tx,ty)
            if not tile:
                return self.die(404)
            idx = query.query(tile,px=ox,py=oy)
            if idx> 2:
                ids = self.ts.ids.ids
                ids = zlib.decompress(ids)
                id = ids.split(',')[idx-2]
                json = '{ "idx":%d,"region_id":"%s"}'%(idx,id)
                callback = self.request.REQUEST.get('callback')
                if callback:
                    json = "%s(%s)"%(callback,json)
                self.write(json)
            else: 
                return
        except:
            self.write('Sorry, there was an error')
            #return self.die(500)
            raise
def gTileBounds(gmerc_bounds,zoom):
    """ gTileBounds returns the bounds of the map in the gTile scheme. 
    """
    SPHEREMERC_GROUND_SIZE = (20037508.34*2)
    zoomfactor = 2**zoom
    tilesize = SPHEREMERC_GROUND_SIZE / zoomfactor
    minx,miny,maxx,maxy = gmerc_bounds
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
    return map(int,[leftx,topy,rightx,boty,zoom])


def get_application(prefix='',debug=False):
    """
    Returns a WSGI compliant application.
    
    Arguments:
    prefix -- string -- (optional) URL prefix, do not include the trailing slash.
    debug -- bool -- Disable/Enable debugging.
    """
    application = webapp.WSGIApplication([
                                          (prefix+r'/gmap.*',GMapHandler),
                                          (prefix+r'/query.*', QueryHandler),
                                          (prefix+r'/classify.*', ClassifyHandler),
                                          (prefix+r'/colors.*',ColorSchemeHandler),
                                          (prefix+r'/legend.*',LegendHandler),
                                          (prefix+r'/o.png.*', OverviewHandler),
                                          (prefix+r'/o/.*', OverviewHandler),
                                          (prefix+r'/ids.csv.*', TileSetIdsHandler),
                                          (prefix+r'/m/.*', TileSetHandler),
                                          (prefix+r'/t/.*', TileHandler),
                                          (prefix+r'/.*', DTMHandler),
                                        ], debug=debug)
    return application
