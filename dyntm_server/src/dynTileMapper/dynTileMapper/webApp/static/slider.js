// Opacity control stuff including slider (after Mike Williams)
// == Create a Custom GControl ==
function XSliderControl(layer,i,slideSrc,knobSrc) {
    this.layer = layer;
    this.init = i;//initial slider position 
    this.slideImg = new Image();
    this.slideImg.src = slideSrc;
    this.knobImg = new Image();
    this.knobImg.src = knobSrc;
    //var len = this.slideImg.width-this.knobImg.width;
    var len = 74-19;
    this.len = len;
    this.timer = false;
}
XSliderControl.prototype = new GControl();
// == This function positions the slider to match the specified opacity ==
XSliderControl.prototype.setSlider = function(opacity) {
    var left = Math.round((this.len*opacity));
    this.draggable_knob.left = left;
    this.knob.style.left = left+"px";
}

// == This function reads the slider and sets the overlay opacity level ==
XSliderControl.prototype.setOpacity = function() {
    var o = this.draggable_knob.left/this.len;       
    this.layer.getOpacity = function () {return o;};
    var cur = this.map.getCurrentMapType();
    this.map.setMapType(G_NORMAL_MAP);
    this.map.setMapType(cur);
    if (this.timer) { this.timer = false; }
   
}
// Set a short timer to prevent too many setOpacity events from being fired.
XSliderControl.prototype.setOpacityEvt = function() {
    if (!(this.timer)) {
	var that = this;
	this.timer = setTimeout(function (){that.setOpacity()},200);
    }
}



// == This gets called by the API when addControl(new XSlider()) is used ==
XSliderControl.prototype.initialize = function(map) {
    // obtain Function Closure on a reference to "this"
    var that=this;
    // store a reference to the map so that we can make calls on it
    this.map = map;

    // Is this MSIE, if so we need to use AlphaImageLoader
    var agent = navigator.userAgent.toLowerCase();

    // create the background graphic as a <div> containing an image
    var container = document.createElement("div");
    container.style.width="74px";//this.slideImg.width+"px";
    container.style.height="19px";//this.slideImg.height+"px";
    var slide = document.createElement("div")
    slide.style.backgroundImage = "url("+this.slideImg.src+")";
    slide.style.width="74px";//this.slideImg.width+"px";
    slide.style.height="19px";//this.slideImg.height+"px";
    this.knob = document.createElement("img"); 
    this.knob.src = this.knobImg.src;
    this.knob.height = 19;//this.knobImg.height;
    this.knob.width = 19;//this.knobImg.width;
    slide.appendChild(this.knob);
    //container.innerHTML = '<img src="'+this.slideImg.src+'" width='+this.slideImg.width+' height='+this.slideImg.height+' >';

    // create the knob as a GDraggableObject
    this.draggable_knob=new GDraggableObject(this.knob, {container:slide});
    container.appendChild(slide);
    this.container = container;

    // attach the control to the map
    map.getContainer().appendChild(container);

    // init slider
    this.setSlider(this.init);

    // Listen for the slider being moved and set the opacity
    GEvent.addListener(this.draggable_knob, "drag", function() {that.setOpacityEvt()});

    // Listen for map being changed to show / hide slider
    GEvent.addListener(this.map, "maptypechanged", function() {
        cur = that.map.getCurrentMapType();
        layers = cur.getTileLayers();
        show = false;
        for (x in layers){ if (layers[x] == that.layer){ show = true; } }
        if (show){
            that.knob.style.display="";
            that.container.style.display="";
        } else {
            that.knob.style.display="none";
            that.container.style.display="none";
        }
    });


    return container;
}

// == Set the default position for the control ==
XSliderControl.prototype.getDefaultPosition = function() {
    return new GControlPosition(G_ANCHOR_TOP_RIGHT, new GSize(7, 7));
}
