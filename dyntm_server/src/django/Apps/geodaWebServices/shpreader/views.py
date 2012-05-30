from django.http import HttpResponse
from django.template import Template
from geodaWebServices import WebService
import pysal
import numpy

TEMPLATE = """<html>
<head>
<script>
var polys;
var W;
function onBody(){
	var n = {{len}};
	var stretch = Math.round((16*16*16-1)/n);
	var p = {{polygons}};
	W = {{W}};
	polys = p;
	
	var c = document.getElementById("map");
	var bitmap_colors = [];
	var colors = [];
	for (var i=0; i<n; i++){
		color = ((stretch*i).toString(16));
		while (color.length < 3) {
			color = "0"+color;
		}
		colors[i] = color;
		A = ("0"+(i+0).toString(16)).slice(-2);
		B = ("0"+(i+15).toString(16)).slice(-2);
		C = ("0"+(i+0).toString(16)).slice(-2);
        console.log(A+B+C);
		bitmap_colors[i] = A+B+C;
	}
	//alert(colors);
	drawMap(p,c,n,colors);
	var bitmap = document.getElementById("bitmap");
	//alert(bitmap_colors);
    console.log(bitmap_colors)
	drawMap(p,bitmap,n,bitmap_colors);
}
function drawMap(polygons,canvas,n,colors){
	if (canvas.getContext){
		var ctx = canvas.getContext("2d");
		ctx.clearRect(0,0,{{width}},{{height}});
		ctx.strokeStyle = '#000000';
		for (var i=0; i<n; i++){
			poly = polygons[i]
			ctx.beginPath();
			ctx.fillStyle = '#'+colors[i];
			ctx.moveTo(poly[0][0],poly[0][1]);
			for (var j=1; j<poly.length; j++){
				ctx.lineTo(poly[j][0],poly[j][1]);
			}
			ctx.fill();
			ctx.stroke();
			ctx.closePath();
		}
		canvas.onmousemove = canvasMouse;
	}else{
		alert('No Canvas Support!');
	}
}
function canvasMouse(evt){
	if(evt.offsetX) {
		x = evt.offsetX;
		y = evt.offsetY;
	} else {
		x = evt.clientX;
		y = evt.clientY;
	}
	ctx = document.getElementById("bitmap").getContext('2d');
	img = ctx.getImageData(0,0,{{width}},{{height}});
	offset = y*({{width}}*4)+x*4;
	A = img.data[offset];
	B = img.data[offset+1]-15;
	C = img.data[offset+2]-0;
	s = x + ", " +y + "<br>"+A+','+B+','+C;
	s += "<br>"+
evt.x
+','+
evt.clientX
+','+
evt.offsetX
+','+
evt.layerX
+','+
evt.pageX;
	//document.getElementById('status').innerHTML = s;

	canvas = document.getElementById("map");
	colors = [];
	for (var i=0; i<78; i++){
		colors[i] = "ccc";
	}
	if ((A==B)&&(B==C)){
		colors[A] = "f00";
		if (W) {
			neighbors = W[A];
			for (var j=0; j<neighbors.length; j++){
				colors[neighbors[j]] = "0ff";
			}
		}
	    drawMap(polys,canvas,78,colors);
	}
}
</script>
</head>
<body onLoad='onBody();'>
<canvas id="map" width="{{width}}" height="{{height}}"></canvas>
<div id="status"></div>
<div id='hidden' style="width:0; height:0; overflow:shown">
<canvas id="bitmap" width="{{width}}" height="{{height}}"></canvas>
</div>
</body></html>

"""

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
