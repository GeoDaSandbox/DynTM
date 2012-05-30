import models
import base64

TILE_TYPES = {'A':0,'B':1,'C':2,'D':3}
if __name__=='__main__':
    tileData = '/Users/charlie/Documents/data/stl_hom/stl_hom_cache.csv'
    f = open(tileData,'r')
    print f.next() #header
    for line in f:
        z,x,y,tileType,tile = line.strip().split(',')
        tilename = '%s+%s+%s'%(z,x,y)
        t = models.Tile(tilename)
        t.tileType = TILE_TYPES[tileType]
        if tileType=='B':
            dat = ''.join([i for i in tile if i.isdigit()])
            dat = int(dat)
            t.dat = dat
        else:
            t.dat = base64.b64decode(tile)
        print t.put()
    f.close()
        
