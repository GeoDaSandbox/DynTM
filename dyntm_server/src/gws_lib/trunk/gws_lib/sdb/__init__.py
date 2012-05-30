"""
Dynamic Tile Mapper Database backend for Amazon Web Services SimpleDB

Expects:
aws_accesskeyid and aws_accesskey to be defined.
"""
import os.path
import cPickle
import random
import boto
import simpledb
from base64 import b64decode,b64encode
import zlib
from math import ceil

#import logging
#logging.basicConfig(filename="boto.log", level=logging.DEBUG)
#log = logging.getLogger('boto')

class dbProperty(object):
    typ = str
    def __init__(self,*args,**kwargs):
        pass
    def tostring(self,val):
        return b64encode(str(val))
    def fromstring(self,s):
        return self.typ(b64decode(s))
    #def __new__(cls,*args,**kwargs):
    #    return cls.typ()
class ByteString(str):
    typ = str
class ByteStringProperty(dbProperty):
    typ = str
class BlobProperty(dbProperty):
    def tostring(self,val):
        return b64encode(zlib.compress(val))
    def fromstring(self,s):
        return zlib.decompress(b64decode(s))
    typ = str
class IntegerProperty(dbProperty):
    typ = int
class StringProperty(dbProperty):
    typ = str
class UserProperty(dbProperty):
    typ = str
class BooleanProperty(dbProperty):
    def tostring(self,val):
        return b64encode(str(val))
    def fromstring(self,s):
        return {'True':True,'False':False}[b64decode(s)]
    typ = bool
class DateTimeProperty(dbProperty):
    typ = float
class ReferenceProperty(dbProperty):
    typ = str
class FloatProperty(dbProperty):
    typ = float
class ListProperty(dbProperty):
    def __init__(self,*args,**kwargs):
        if 'item_type' in kwargs:
            self.item_type = kwargs['item_type']
        else:
            self.item_type = StringProperty
    def tostring(self,val):
        #return b64encode('|'.join(map(self.item_type.tostring,val)))
        return b64encode('|'.join(map(str,val)))
    def fromstring(self,s):
        #return map(self.item_type.fromstring,b64decode(s).split('|'))
        return map(self.item_type,b64decode(s).split('|'))
    typ = list

def absProp(tag,prop):
    if not issubclass(type(tag),basestring):
        return None
    def fget(self,tag=tag):
        if tag in self._modelData:
            return prop.fromstring(self._modelData[tag])
        else:
            return ''
    def fset(self,value,tag=tag):
        self._modelData[tag] = prop.tostring(value)
    def fdel(self,tag=tag):
        if tag in self._modelData:
            del self._modelData[tag]
    return property(fget=fget,fset=fset,fdel=fdel)
    #return property(**locals())

class Model:
    class __metaclass__(type):
        def __new__(mcs, name, bases, d):
            #print
            #print "*****************************************"
            #print "******** THE META CLASS IS HERE *********"
            #print "*****************************************"
            #print "mcs:", mcs
            #print "name: ", name
            #print "Bases: ", bases
            ##print "Dict: ", d
            for key in d:
                if issubclass(type(d[key]),dbProperty):
                    #print "Property: ", key, d[key]
                    d[key] = absProp(key,d[key])
            #print
            return type.__new__(mcs, name, bases, d)
    def __init__(self,key_name=None):
        if key_name:
            key_name = key_name
        else:
            key_name = str(random.random())[2:]
        self.key_name = key_name
        self._modelData = {}
    def __repr__(self):
        return "<%s: %s>"%(self.modelType(),self.key_name)
    def as_dict(self):
        return dict([(key,self.__getattribute__(key)) for key in self._modelData.keys()])

    def key(self):
        return self.key_name
    @classmethod
    def modelType(cls):
        #return 'testing'
        return cls.__name__
    def splitModelData(self):
        dat = {}
        for key,val in self._modelData.iteritems():
            size = len(val)
            if size > 1024:
                n = int(ceil(size/1024.0))
                dat[key+'PARTS'] = n
                for i in range(n):
                    dat[key+'PART%d'%i] = val[i*1024:(i+1)*1024]
            else:
                dat[key] = val
        return dat
    def joinModelData(self,dat):
        keys = dat.keys()
        keys = [k for k in keys if k.endswith('PARTS')]
        for key in keys:
            n = int(dat[key])
            base = key[:-5]
            s = ''
            for i in range(n):
                s+= dat[base+'PART%d'%i]
                del dat[base+'PART%d'%i]
            self._modelData[base] = s
            del dat[key]
        self._modelData.update(dat)
        return self
    def put(self):
        modelData = self.splitModelData()
        sdb_conn = boto.connect_sdb(aws_accesskeyid, aws_accesskey)
        sdb_conn.delete_attributes(self.modelType(),self.key_name)
        sdb_conn.put_attributes(self.modelType(),self.key_name,modelData)
        return self.key_name
    @classmethod
    def _install(cls):
        sdb_conn = boto.connect_sdb(aws_accesskeyid, aws_accesskey)
        if not sdb_conn.lookup(cls.modelType()):
            sdb_conn.create_domain(cls.modelType())
    @classmethod
    def get_by_key_name(cls,key_name):
        #log.warn('CONNECT TO SDB')
        #sdb_conn = boto.connect_sdb(aws_accesskeyid, aws_accesskey)
        #log.warn('CONNECT TO SDB using mine.')
        sdb_conn = simpledb.AWS_SimpleDB(aws_accesskeyid,aws_accesskey)
        #db_key_name = cls.modelType()+':'+key_name
        try:
            obj = cls(key_name)
            #log.warn('SDB.GET_ATTR')
            dat = sdb_conn.get_attributes(cls.modelType(),key_name)
            #log.warn('mine.get_itme')
            #dat = sdb_conn.get_item(cls.modelType(),key_name)
            #print "HERE",dat
            if dat:
                obj.joinModelData(dat)
                return obj
            else:
                #print "No object data was found..."
                #print aws_accesskeyid, aws_accesskey
                #print sdb_conn
                #print cls.modelType()
                #print key_name
                #print dat
                raise ValueError,'not found' # this is slow, use if/else
        except:
            return None
            #return None
    get = get_by_key_name
    @classmethod
    def get_or_create(cls,key_name):
        created = False
        try:
            obj = cls.get(key_name)
            if not obj:
                obj = cls(key_name)
                obj.put()
                created = True
            return obj,created
        except:
            raise
            return None,created
    @classmethod
    def all(cls,keys_only=False):
        sdb_conn = boto.connect_sdb(aws_accesskeyid, aws_accesskey)
        domain = cls.modelType()
        if keys_only:
            q = sdb_conn.select(domain, "select itemName() from %s"%domain)
            keys = [x.name for x in q]
            return DBQuery(cls,keys=keys,keys_only=True)
        else:
            return [cls(itm.name).joinModelData(itm) for itm in sdb_conn.get_domain(domain)]
        #start = len(cls.modelType())+1
        #keys = [f[start:-4] for f in os.listdir(DB) if f.startswith(cls.modelType())]
        #if keys_only:
        #    return DBQuery(cls,keys=keys,keys_only=True)
        #return [cls.get_by_key_name(key) for key in keys]
    @classmethod
    def select(cls,prop,value,keys_only=False):
        sdb_conn = boto.connect_sdb(aws_accesskeyid, aws_accesskey)
        domain = cls.modelType()
        if keys_only:
            q = sdb_conn.select(domain, "select itemName() from %s where %s='%s'"%(domain,prop,b64encode(value)))
            return [x.name for x in q]
        else:
            q = sdb_conn.select(domain, "select * from %s where %s='%s'"%(domain,prop,b64encode(value)))
            return [cls(itm.name).joinModelData(itm) for itm in q]
    def delete(self):
        sdb_conn = boto.connect_sdb(aws_accesskeyid, aws_accesskey)
        domain = sdb_conn.get_domain(self.modelType())
        item = domain.get_item(self.key_name)
        item.delete()

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

