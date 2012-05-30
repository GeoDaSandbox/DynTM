#!/usr/bin/env python
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from models import TileSet,Tile,Classification,ColorScheme
from render import render,classification,colors,query
from google.appengine.api.labs import taskqueue
import zlib
import array
UNSIGNED_ITEM_TYPES = {array.array('B').itemsize:'B', array.array('H').itemsize:'H', array.array('I').itemsize:'I', array.array('L').itemsize:'L'}
import logging

from dtm import DTMHandler
INDEX_BATCH_SIZE = 200
class TaskHandler(DTMHandler):
    def delete(self):
        self._ts = None
        self._cl = None
        self._cs = None
        self._tile = None
        return self.real_delete()
    def real_get(self):
        self.response.out.write('get')

class Remove(TaskHandler):
    def real_get(self):
        ts = self.ts
        if not ts:
            self.write("no ts")
        else:
            name = ts.name
            self.write("<html><head><title>")
            self.write("Cleaning up TileSet: %s"%name)
            self.write("</title></head><body>")
            self.write("<h1> Found TileSet: %s</h1><hr />"%name)
            #Overview
            self.remove_overview()
            #Classifications
            self.remove_classifications()
            #TileSetIDS
            try:
                ts.ids.delete()
                self.write("<b>Remove TileSetIDS: DONE.</b><br>")
            except:
                self.write("<b>Remove TileSetIDS: DONE.</b><br>")
            #Tiles
            self.write("<b>Remove Tiles: </b>")
            count = memcache.get("delcount:%s"%name)
            if count is not None:
                if count > 0:
                    self.write("%d Tiles Removed..."%count)
                elif count == -99:
                    self.write("<b>DONE.</b>")
            else:
                self.write("Queued.")
                taskqueue.add(url='/quedetask/remove',params={'ts':name},method='DELETE')
            #TileSet
            ts.delete()
            self.write("<br /><b>Remove TileSet:</b>DONE.<br>")
    def remove_classifications(self):
        q = Classification.all(keys_only=True)
        q.filter('tileset',self.ts) 
        if q.count():
            db.delete(q.fetch(INDEX_BATCH_SIZE))
            self.write("<b>Remove Classifications:</b>Removing, refresh until done.<br />")
        else:
            self.write("<b>Remove Classifications: DONE.</b><br />")

    def remove_overview(self):
        ts = self.ts
        if ts:
            try:
                o = ts.overview
            except:
                self.write("<b>Remove Overview:</b> Not Found. </b><br />")
                return
            try:
                overview_key = ts.overview.key()
                db.delete(overview_key)
                self.write("<b>Remove Overview:</b> <del>%s</del> <b> DONE. </b><br />"%overview_key)
            except:
                self.write("<b>Remove Overview:</b> <b> FAILED. </b><br />")
    def real_delete(self):
        logging.info("DELETE")
        ts = self.ts
        if not ts:
            self.die(500)
        else:
            name = ts.name
            key = db.Key.from_path('Tile','t:%s:0+0+0'%name)
            q = db.GqlQuery("SELECT __key__ from Tile WHERE __key__ >= :1 ORDER BY __key__",key)
            count = memcache.get("delcount:%s"%name)
            if count is None:
                if not memcache.set("delcount:%s"%name,0,3600):
                    logging.info('memcache fail')
                else:
                    count = 0
            if q.count() > 0:
                keys = q.fetch(INDEX_BATCH_SIZE)
                keys = [k for k in keys if name in k.name()]
                n = len(keys)
                if n == 0:
                    logging.info('Delete Tiles, Done with: %s'%name)
                    memcache.set("delcount:%s"%name,-99,3600)
                    
                    return
                last_key = keys[-1]
                logging.info('Delete Tiles, last: %s'%last_key.name())
                db.delete(keys)
                memcache.set("delcount:%s"%name,count+n,3600)
                taskqueue.add(url='/quedetask/remove',params={'ts':name},method='DELETE')
            else: #NO Tiles Left (AT ALL)
                logging.info('Delete Tiles, Done with: %s'%name)
                memcache.set("delcount:%s"%name,-99,3600)

            


def main():
    application = webapp.WSGIApplication([
                                          (r'/tasks/remove',Remove),
                                        ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)
if __name__ == '__main__': main()
