from django.http import HttpResponse
from django.template import Template
from geodaWebServices import WebService
import pysal
import numpy

TEMPLATE = """TEMPLATE_PLACE_HOLDER"""

class ShpReader(WebService):
    SHPS = {'stlhom':'/Users/charlie/Documents/data/stl_hom/stl_hom.shp','usa':'/Users/charlie/Documents/data/usa/usa.shp'}
    def __init__(self,format='html'):
        t = Template(TEMPLATE)
        WebService.__init__(self,format,t)
    def get(self,shpName='',width=0,height=0):
        print shpName,width,height
        if not shpName in self.SHPS:
            return self.index()
        shp = pysal.open(self.SHPS[shpName])
        W = None
        if 'w' in self.request.GET:
            wtype = self.request.GET['w']
            if wtype.lower() == 'rook':
                W = pysal.rook_from_shapefile(self.SHPS[shpName])
            elif wtype.lower() == 'queen':
                W = pysal.queen_from_shapefile(self.SHPS[shpName])
            else:
                try:
                    k = int(wtype)
                    W = pysal.knnW_from_shapefile(self.SHPS[shpName],k)
                except:
                    print "No valid W"
        print shp
        if width and height:
            width=int(width)
            height=int(height)
            if W:
                return self.write({'len':len(shp), 'polygons':shift_scale_shp(shp,width,height),'width':width,'height':height,'W':W.neighbors})
            else:
                return self.write({'len':len(shp), 'polygons':shift_scale_shp(shp,width,height),'width':width,'height':height,'W':'null'})
        return self.write({'len':len(shp)})
    def index(self):
        # This should be a template for the web service's home page. (if there is one)
        return HttpResponse('Welcome to my Shp Reader Web Service!')

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
def shift_scale_shp(shp,width,height):
    x,y,X,Y = shp.bbox
    rx = X-x
    ry = Y-y
    scale = max(rx,ry)
    unscale = min(width,height)
    c=0
    d=0
    e=0
    data = {}
    for i,poly in enumerate(shp):
        spoly = []
        prev_vt = None
        for vx,vy in poly.vertices:
            sx = (vx-x)/scale
            sy = 1-((vy-y)/scale)
            vert = map(int,(round(sx*unscale),round(sy*unscale)))
            if vert == prev_vt:
                d+=1
            else:
                c+=1
                prev_vt = vert
                spoly.append(vert)
        pts = drop_colin(spoly)
        e += len(spoly)-len(pts)
        data[i] = pts
    print "Kept: %d, Dropped Iden: %d, Dropped Colin:%d"%(c,d,e)
    return data
