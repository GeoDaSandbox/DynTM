import pysal
import mapscript
import tempfile
import os

#GMERC = ms.projectionObj('init=epsg:900913')
GMERC = ms.projectionObj('init=epsg:3857')
WGS84 = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs '


def shp2model(shp,shx,dbf):
    shpf = tempfile.NamedTemporaryFile('wb', suffix='.shp',delete=False)
    shpf.write(shp)
    shpf.close()
    shxf = open(shpf.name[:-3]+'shx','wb')
    shxf.write(shx)
    shxf.close()
    dbff = open(shpf.name[:-3]+'dbf','wb')
    dbff.write(dbf)
    dbff.close()
    names = [x.name for x in shpf,shxf,dbff]
    print names
    shp = pysal.open(names[0],'r')
    x = shp.header['BBOX Xmin']
    y = shp.header['BBOX Ymin']
    X = shp.header['BBOX Xmax']
    Y = shp.header['BBOX Ymax']
    cx = (x+X)/2.0
    cy = (y+Y)/2.0

    dbf = pysal.open(names[2],'r')

    data = {}
    data['name'] = "TEST_TILES"
    data['notes'] = "Notes are currently not supported"
    data['source'] = "Source is currently not supported"
    data['owner'] = "charlie.spam@asu.edu"
    data['public'] = True
    data['overview'] = None
    data['idName'] = None
    data['idlen'] = len(shp)
    data['ids'] = range(len(shp))
    data['cLat'] = cy
    data['cLng'] = cx
    data['minx'] = x
    data['miny'] = y
    data['maxx'] = X
    data['maxy'] = Y
    data['GMERC_BOUNDS'] = gmerc_bounds_fromWGS84(x,y,X,Y)
    data['maxZoom'] = 20
    print map(os.remove,names)
    return data

def gmerc_bounds_fromWGS84(x,y,X,Y):
    """ TODO """
    return [0,0,1,1]

    


    
if __name__=='__main__':
    shp = open("../../../example_data/stl_hom/stl_hom.shp","rb").read()
    shx = open("../../../example_data/stl_hom/stl_hom.shx","rb").read()
    dbf = open("../../../example_data/stl_hom/stl_hom.dbf","rb").read()
    model = shp2model(shp,shx,dbf)
