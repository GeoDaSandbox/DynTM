from math import floor,ceil
# 3rd Party
import numpy
import pysal
import mapscript

ID_OFFSET = 2 #background and borders
SPHEREMERC_GROUND_SIZE = (20037508.34*2)
WGS84 = mapscript.projectionObj('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs ')
GMERC = mapscript.projectionObj('init=epsg:3857')

def drop_colin(pts):
    i = len(pts)-3
    bad = []
    while i:
        a,b,c = numpy.array(pts[i:i+3])
        if numpy.cross(a-b,c-b) == 0:
            bad.append(i+1)
        i-=1
    pts = [pts[i] for i in range(len(pts)) if i not in bad]
    bad = []
    return pts 
def clean_poly(pts,zoom):
    zoomfactor = 2**zoom
    tilesize = SPHEREMERC_GROUND_SIZE / zoomfactor
    clean_pts = []
    prev_pt = None
    for pt in pts:
        x = 256*((pt.x+(SPHEREMERC_GROUND_SIZE/2.0))/tilesize)
        y = 256*((-1*(pt.y-(SPHEREMERC_GROUND_SIZE / 2.0)))/tilesize)
        vert = (int(round(x)),int(round(y)))
        if vert == prev_pt:
            pass
        else:
            clean_pts.append(vert)
        prev_pt = vert
    if len(clean_pts)>=3:
        clean_pts = drop_colin(clean_pts)
    return clean_pts

def shp2json(shp_path,zoom=0):
    shp = pysal.open(shp_path,'r')
    data = {}
    tile2poly = {}
    for i,poly in enumerate(shp):
        parts = []
        holes = []
        for part in poly.parts:
            pts = [mapscript.pointObj(*pt) for pt in part]
            [pt.project(WGS84,GMERC) for pt in pts]
            pts = clean_poly(pts,zoom)
            part = {'n':len(pts),'x':[x[0] for x in pts],'y':[x[1] for x in pts]}
            add = True
            for existing in parts:
                if part == existing:
                    add = False
            if add: parts.append(part)
        for hole in poly.holes:
            if hole:
                pts = [mapscript.pointObj(*pt) for pt in hole]
                [pt.project(WGS84,GMERC) for pt in pts]
                pts = clean_poly(pts,zoom)
                pts = pts[::-1] # reverse the holes for Canvas drawing, see non-zero winding rule.
                hole = {'n':len(pts),'x':[x[0] for x in pts],'y':[x[1] for x in pts]}
                add = True
                for existing in holes:
                    if hole == existing:
                        add = False
                if add: holes.append(hole)
        ###
        # Find All the tiles this polygon covers (bbox approximation).
        ###
        bbox = poly.bounding_box
        ll = mapscript.pointObj(bbox.left,bbox.lower)
        ll.project(WGS84,GMERC)
        minX,maxY = merc2gtilecoord(ll.x,ll.y,zoom) #Max Y is the lowest Y
        minX = int(floor(minX*256))
        maxY = int(ceil(maxY*256))
        ur = mapscript.pointObj(bbox.right,bbox.upper)
        ur.project(WGS84,GMERC)
        maxX,minY = merc2gtilecoord(ur.x,ur.y,zoom)
        maxX = int(ceil(maxX*256))
        minY = int(floor(minY*256))
        tiles = []
        #for x in range(minX,maxX+1):
        #    for y in range(minY,maxY+1):
        #        tid = "%d:%d:%d"%(zoom,x,y)
        #        tiles.append(tid)
        #        if tid not in tile2poly:
        #            tile2poly[tid] = []
        #        tile2poly[tid].append(i+ID_OFFSET)
        
        #tiles = set([(x/256,y/256) for x,y in clean_pts])
        #for tile in tiles:
        #    tid = "%d:%d:%d"%(zoom,tile[0],tile[1])
        #    if tid not in tile2poly:
        #        tile2poly[tid] = []
        #    tile2poly[tid].append(i+ID_OFFSET)
        d = {'np':len(parts),
            'nh':len(holes),
            #'tiles':tiles,
            'bbox':[minX,minY,maxX,maxY] }
        if d['np'] > 0:
            d['parts'] = parts
        if d['nh'] >0:
            d['holes'] =holes
        data[i+ID_OFFSET] = d
    data['n'] = len(data)
    data['zoom'] = zoom
    #data['byTile'] = tile2poly
    return data

def merc2gtilecoord(x,y,zoom):
    zoomfactor = 2**zoom
    tilesize = SPHEREMERC_GROUND_SIZE / zoomfactor
    return ((x+(SPHEREMERC_GROUND_SIZE/2.0))/tilesize), ((-1*(y-(SPHEREMERC_GROUND_SIZE / 2.0)))/tilesize)
