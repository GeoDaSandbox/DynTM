import sys
import traceback
import tempfile
import os.path
import cPickle
import random
from dynTileMapper.dtm_wsgi import msRender
#DB = tempfile.mkdtemp()
#DB = '/var/folders/Tr/TrZxqK-GGOui5bZYkIO03E+++TI/-Tmp-/tmphQI0V_'
#print "DB location is: ",DB


class dbProperty(object):
    typ = str
    def __new__(cls,*args,**kwargs):
        return cls.typ()
class ByteString(str):
    typ = str
class ByteStringProperty(dbProperty):
    typ = str
class BlobProperty(dbProperty):
    typ = str
class IntegerProperty(dbProperty):
    typ = int
class StringProperty(dbProperty):
    typ = str
class UserProperty(dbProperty):
    typ = str
class BooleanProperty(dbProperty):
    typ = bool
class DateTimeProperty(dbProperty):
    typ = str
class ReferenceProperty(dbProperty):
    typ = str
class FloatProperty(dbProperty):
    typ = float
class ListProperty(dbProperty):
    typ = list

class Model:
    def __init__(self,key_name=None):
        if key_name:
            key_name = key_name
        else:
            key_name = str(random.random())[2:]
        self.key_name = key_name
    def __repr__(self):
        return self.key_name
    def key(self):
        return self.key_name
    @classmethod
    def modelType(cls):
        return cls.__name__
    @property
    def fname(self):
        key_name = self.modelType()+':'+self.key_name
        return os.path.join(DB,key_name+'.dat')
    def put(self):
        f = open(self.fname,'wb')
        cPickle.dump(self,f,-1)
        f.close()
        return self.key_name
    @classmethod
    def get_by_key_name(cls,key_name):
        db_key_name = cls.modelType()+':'+key_name
        try:
            fname = os.path.join(DB,db_key_name+'.dat')
            f = open(fname,'rb')
            obj = cPickle.load(f)
            f.close()
            return obj
        except:
            try:
                return cls.create_by_key_name(key_name)
            except IOError:
                raise
                return None
            #return None
    get = get_by_key_name
    @classmethod
    def create_by_key_name(cls,key_name):
        if cls.modelType() == 'Tile':
            try:
                # t:stlhom:z+x+y
                t,ts,zxy = key_name.split(':')
                z,x,y = map(int,zxy.split('+'))
                tile = msRender.tile_from_ms(ts,z,x,y)
                return tile
            except:
                raise IOError,'Tile not found'
        elif cls.modelType() == 'TileSet':
            try:
                # ts:stlhom
                t,name = key_name.split(':')
                return msRender.tileSet_from_yaml(name)
            except:
                raise IOError,'TileSet not found'
                raise
        return None
    @classmethod
    def all(cls,keys_only=False):
        start = len(cls.modelType())+1
        keys = [f[start:-4] for f in os.listdir(DB) if f.startswith(cls.modelType())]
        if keys_only:
            return DBQuery(cls,keys=keys,keys_only=True)
        return [cls.get_by_key_name(key) for key in keys]
    def delete(self):
        os.remove(self.fname)

class DBQuery:
    def __init__(self,model,keys=None,models=None,keys_only=False):
        self.model = model
        self.keys = keys
        self.models = models
        self.keys_only = keys_only
    def filter(self,prop,value):
        if self.keys and not self.models:
            self.models = [self.model.get_by_key_name(key) for key in self.keys]
        if self.count():
            self.models = [m for m in self.models if hasattr(m,prop)]
            self.models = [m for m in self.models if getattr(m,prop)==value]
            self.keys = [m.key_name for m in self.models]
    def count(self):
        return len(self.keys)
    def __iter__(self):
        if self.keys_only:
            return self.keys.__iter__()
        else:
            return self.models.__iter__()

if __name__=='__main__':
    import os
    m = Model()
    m.put()
    print os.listdir(DB)
    m.delete()
    print os.listdir(DB)

