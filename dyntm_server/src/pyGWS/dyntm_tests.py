from math import floor,ceil
from DynTM import GeoDaWS_DynTM
import time
import urllib

DEBUG = True

def load_gtile(count,ts_extent,save=False):
    url = 'http://mt0.google.com/vt/x=%d&y=%d&z=%d'
    c = 0
    dl_time = 0.0
    dl_size = 0
    all_start = time.time()
    for tile in tiles_from_extent(ts_extent):
        z,x,y = tile
        dl_start = time.time()
        u = urllib.urlopen(url%(x,y,z))
        png = u.read()
        dl_stop = time.time()
        dl_time += (dl_stop-dl_start)
        dl_size += len(png)
        if png[:4] == '\x89PNG':
            if DEBUG: print "Got",tile,len(png),"bytes in %0.5f seconds."%(dl_stop-dl_start)
        else:
            print "ERROR WITH:",tile," (got in %0.5f seconds.)"%(dl_stop-dl_start)
        if save:
            open('tiles/google:%d+%d+%d.png'%(z,x,y),'wb').write(png)
        c+=1
        if c >= count:
            break
    all_stop = time.time()
    print "Got %d tiles in %0.5f seconds."%(count,all_stop-all_start)
    print "%0.5f of %0.5f seconds spent on download."%(dl_time,all_stop-all_start)
    print "Average speed: %0.8f bytes/second"%(dl_size/dl_time)
    print dl_size,dl_time
        
def load_tiles2(ts,ts_extent, count=50,cl=None,cs=None,base='http://apps.geodacenter.org'):
    url = base+'/dyntm/t/?ts=%(ts)s&z=%(z)d&x=%(x)d&y=%(y)d'
    dat = {'z':0,'x':0,'y':0,'ts':ts}
    c = 0
    dl_time = 0.0
    dl_size = 0
    all_start = time.time()
    for tile in tiles_from_extent(ts_extent):
        z,x,y = tile
        dat['z'] = z
        dat['x'] = x
        dat['y'] = y
        t_url = url%dat
        if cl:
            t_url+= '&cl=%s'%cl
        if cs:
            t_url+= '&cs=%s'%cs
        dl_start = time.time()
        u = urllib.urlopen(t_url)
        png = u.read()
        dl_stop = time.time()
        dl_time += (dl_stop-dl_start)
        dl_size += len(png)
        if png[:4] == '\x89PNG':
            if DEBUG: print "Got",tile,len(png),"bytes in %0.5f seconds."%(dl_stop-dl_start)
        else:
            print "ERROR WITH:",tile," (got in %0.5f seconds.)"%(dl_stop-dl_start)
        c+=1
        if c >= count:
            break
    all_stop = time.time()
    print "Got %d tiles in %0.5f seconds."%(count,all_stop-all_start)
    print "%0.5f of %0.5f seconds spent on download."%(dl_time,all_stop-all_start)
    print "Average speed: %0.8f bytes/second"%(dl_size/dl_time)
    print dl_size,dl_time
def create_html_page(ts,ts_extent, count=50,cl=None,cs=None):
    header = "<html><head><title>DynTM Test Page</title></head><body>\n"
    body = []
    footer = "</body></html>"
    img = "<img src='%s'>\n"
    base = 'http://apps2.geodacenter.org'
    #base = 'http://ec2-184-72-168-123.compute-1.amazonaws.com'
    #base = 'http://ec2-184-72-157-141.compute-1.amazonaws.com'
    url = base+'/dyntm/t/?ts=%(ts)s&z=%(z)d&x=%(x)d&y=%(y)d'
    dat = {'z':0,'x':0,'y':0,'ts':ts}
    c = 0
    for tile in tiles_from_extent(ts_extent):
        z,x,y = tile
        dat['z'] = z
        dat['x'] = x
        dat['y'] = y
        t_url = url%dat
        if cl:
            t_url+= '&cl=%s'%cl
        if cs:
            t_url+= '&cs=%s'%cs
        c+=1
        if c >= count:
            break
        body.append(img%t_url)
    body.reverse()
    return header+''.join(body)+footer
        
def load_tiles(client, ts, ts_extent, count=50, cl=None, cs=None, save=False):
    c = 0
    dl_time = 0.0
    dl_size = 0
    all_start = time.time()
    for tile in tiles_from_extent(ts_extent):
        z,x,y = tile
        dl_start = time.time()
        png = client.getTile(ts,z,x,y,clid=cl,csid=cs)
        dl_stop = time.time()
        dl_time += (dl_stop-dl_start)
        dl_size += len(png)
        if png[:4] == '\x89PNG':
            if DEBUG: print "Got",tile,len(png),"bytes in %0.5f seconds."%(dl_stop-dl_start)
        else:
            print "ERROR WITH:",tile," (got in %0.5f seconds.)"%(dl_stop-dl_start)
        if save:
            open('tiles/%s:%d+%d+%d.png'%(ts,z,x,y),'wb').write(png)
        c+=1
        if c >= count:
            break
    all_stop = time.time()
    print "Got %d tiles in %0.5f seconds."%(count,all_stop-all_start)
    print "%0.5f of %0.5f seconds spent on download."%(dl_time,all_stop-all_start)
    print "Average speed: %0.8f bytes/second"%(dl_size/dl_time)
    print dl_size,dl_time


def gTileBounds(zoom,gmerc_extent):
    """ gTileBounds returns the bounds of the map in the gTile scheme. 
    """
    SPHEREMERC_GROUND_SIZE = (20037508.34*2)
    zoomfactor = 2**zoom
    tilesize = SPHEREMERC_GROUND_SIZE / zoomfactor
    minx,miny,maxx,maxy = gmerc_extent
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

def tiles_from_extent(gmerc_extent,levels=range(20)):
    for zoom in levels:
        left,upper,right,lower = gTileBounds(zoom,gmerc_extent)
        for x in range(left,right+1):
            for y in range(upper,lower+1):
                yield (zoom,x,y)


if __name__=='__main__':
    AccessKeyID = 'charlie4c3d7a00'
    AccessKey = '9ec1733202311e4dc3b11c79e36bede96180b358'
    client = GeoDaWS_DynTM(AccessKeyID=AccessKeyID,AccessKey=AccessKey)

    stl_hom = 'charlie:B9C118EB30A9EAE19C93902E9F01EF8A'
    stl_hom_extentMERC = [-10319392.044500001, 4422645.2980199996, -9786828.0908700004, 4913950.2656699996]
    stl_hom_extentWGS = [-92.700675964400006, 36.881809234599999, -87.9165725708, 40.329566955600001]
    stl_hom_cl = 'charlie:474f117491ba503bde2b1eb2b9a36b3a'
    
    #raw_input()
    #load_tiles(client,stl_hom,stl_hom_extentMERC,count=500,save=True, cl='5')
    #html = create_html_page(stl_hom,stl_hom_extentMERC,count=50,cl=stl_hom_cl)
    #open('test.html','w').write(html)
    #load_gtile(50,stl_hom_extentMERC,save=True)
