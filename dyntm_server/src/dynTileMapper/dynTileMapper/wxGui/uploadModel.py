import os.path
import os
import sys
import StringIO
import base64
import zlib
import yaml
from abstractmodel import AbstractModel
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.tools import appengine_rpc
from google.appengine.tools import bulkloader

from model import M_DyMaps2
from dynTileMapper.dtm_wsgi.models import TileSet,Overview,TileSet_IDS
from dynTileMapper.webApp import Loader

DTM_CONN_TEST_URL = '/users/'
DTM_REMOTE_API_URL = '/remote_api'
TILE_SET_PREFIX = 'ts:'
TILESET_IDS_PREFIX = 'tsids:'
OVERVIEW_PREFIX = 'o:'

def newProp(fnc):
    return property(**fnc())
class M_UploadTiles(AbstractModel):
    """ Data Model for Tile Uploader
    """
    TAGS = ['mapConfig','server','user','passwd','upload']
    # Dictionary to hold model data
    __modelData = {}
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
    server = absProp('server')
    user= absProp('user')
    passwd = absProp('passwd')
    checkTiles = absProp('checkTiles')
    checkMap = absProp('checkMap')
    checkIDS = absProp('checkIDS')
    checkOverview = absProp('checkOverview')

    def _auth(self):
        return (self.user,self.passwd)
    def verify(self):
        rpc = appengine_rpc.HttpRpcServer(self.server,self._auth,None,DTM_CONN_TEST_URL)
        data = rpc.Send(DTM_CONN_TEST_URL,None)
        if 'PostPublic' in data:
            return True
        else:
            return False
    def run(self):
        f = open(self.mapConfig,'r')
        m = yaml.load(f)
        if isinstance(m,M_DyMaps2):
            remote_api_stub.ConfigureRemoteDatastore(None,DTM_REMOTE_API_URL,self._auth,self.server)
            app_id = os.getenv('APPLICATION_ID')
            os.putenv('AUTH_DOMAIN', 'gmail.com')
            if self.checkMap:
                self.checkOverview = True
                self.checkIDS = True
            #PUT OVERVIEW
            if self.checkOverview:
                overview = Overview(key_name=OVERVIEW_PREFIX+m.name)
                overview.typ = m.overview_typ
                overview.dat = base64.b64decode(m.overview_dat)
                overview.width = m.overview_width
                overview.height = m.overview_height
                overview_key = overview.put()
                print overview_key
            #PUT IDS
            if self.checkIDS:
                ids = TileSet_IDS(key_name=TILESET_IDS_PREFIX+m.name)
                ids.ids = zlib.compress(m.ids)
                ids_key = ids.put()
                print ids_key
            #PUT TILESET
            if self.checkMap:
                tile_set = TileSet(key_name=TILE_SET_PREFIX+m.name)
                tile_set.owner = users.User(email=self.user,_auth_domain=self.user.split('@')[1])
                tile_set.name = m.name
                tile_set.notes = m.notes
                tile_set.source = m.source
                tile_set.idName = m.variableNames[m.idVariable]
                tile_set.idlen = len(m.ids.split(','))
                tile_set.cLng = m.cLng
                tile_set.cLat = m.cLat
                tile_set.minx = m.minx
                tile_set.miny = m.miny
                tile_set.maxx = m.maxx
                tile_set.maxy = m.maxy
                tile_set.GMERC_BOUNDS = m.gmerc_bounds
                tile_set.maxZoom = max(m.scales)
                if overview_key:
                    tile_set.overview = overview_key
                if ids_key:
                    tile_set.ids = ids_key
                print tile_set.put()

            #PUT TILES
            if self.checkTiles:
                bulk_args = {}
                bulk_args['url'] = 'http://%s%s'%(self.server,DTM_REMOTE_API_URL)
                bulk_args['filename'] = m.cacheFile
                fname = os.tempnam()
                o = open(fname,'w')
                o.write(Loader.LOADER_FILE)
                o.close()
                bulk_args['config_file'] = fname
                #bulk_args['config_file'] = "../webApp/Loader.py"
                bulk_args['kind'] = 'Tile'
                bulk_args['loader_opts'] = m.name

                #begin google defaults
                bulk_args['batch_size'] = bulkloader.DEFAULT_BATCH_SIZE
                bulk_args['num_threads'] = bulkloader.DEFAULT_THREAD_COUNT
                bulk_args['bandwidth_limit'] = bulkloader.DEFAULT_BANDWIDTH_LIMIT
                bulk_args['rps_limit'] = bulkloader.DEFAULT_RPS_LIMIT
                bulk_args['http_limit'] = bulkloader.DEFAULT_REQUEST_LIMIT
                bulk_args['db_filename'] = None
                bulk_args['app_id'] = app_id
                bulk_args['auth_domain'] = 'gmail.com'
                bulk_args['has_header'] = True
                bulk_args['result_db_filename'] = None
                bulk_args['download'] = False
                bulk_args['exporter_opts'] = None
                bulk_args['debug'] = False
                bulk_args['log_file'] = None
                bulk_args['email'] = self.user
                bulk_args['passin'] = True
                bulk_args['map'] = None #added in SDK 1.2.4
                bulk_args['mapper_opts'] = None #added in SDK 1.2.4
                #end google defaults
                
                stdin = sys.stdin
                sys.stdin = StringIO.StringIO(self.passwd)
                sys.stdin.fileno = stdin.fileno
                bulkloader.Run(bulk_args)
                sys.stidin = stdin
                os.remove(fname)
        else:
            raise TypeError,'Invald Model File'
    @newProp
    def mapConfig():
        tag='mapConfig'
        def fget(self,tag=tag):
            if tag in self.__modelData:
                return self.__modelData[tag]
            else:
                return ''
        def fset(self,value,tag=tag):
            if os.path.exists(value) and not os.path.isdir(value):
                self.__modelData[tag] = value
            else:
                self.__modelData[tag] = False
            self.update(tag)
        def fdel(self,tag=tag):
            del self.__modelData[tag]
        del tag
        return locals()
    def getByTag(self,tag):
        return self.__getattribute__(tag)
    def verbose(self):
        print self.__modelData
    def reset(self):
        self.__modelData = {}
        self.update()
        self.SetModified(False)

