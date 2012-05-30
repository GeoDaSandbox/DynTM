from google.appengine.ext import db
from models import Tile
class Mapper(object):
    KIND = None
    FILTERS = []
    def map(self,entity):
        return ([],[])
    def get_query(self):
        q = self.KIND.all(keys_only=True)
        for prop, value in self.FILTERS:
            q.filter("%s =" % prop, value)
        q.order("__key__")
        return q
    def run(self,batch_size=100):
        c = 0
        q = self.get_query()
        entities = q.fetch(batch_size)
        c+=batch_size
        while entities:
            to_put = []
            to_delete = [e for e in entities if "STLHOM2" in e.key().name()]
            print e.key().name()
            #for entity in entities:
            #    map_updates, map_deletes = self.map(entity)
            #    to_put.extend(map_updates)
            #    to_delete.extend(map_deletes)
            if to_put:
                db.put(to_put)
            if to_delete:
                print to_delete
                db.delete(to_delete)
            q = self.get_query()
            q.filter("__key__ >", entities[-1].key())
            entities = q.fetch(batch_size)
            c+=batch_size
        return True
class BulkTileDelete(Mapper):
    def __init__(self):
        self.KIND = Tile
    def map(self,entity):
        if 'STLHOM2' in entity.key().name():
            return ([],[entity])
        else:
            return ([],[])

class BulkDelete(Mapper):
    def __init__(self,kind):
        self.KIND = kind
    def map(self,entity):
        return ([],[entity])


def clearTiles(n=100):
    deleter = BulkTileDelete()
    while 1:
        try: 
            done = deleter.run(n)
            if done: break
        except Timeout:
            print "[Error, Timeout]"
        except:
            raise
