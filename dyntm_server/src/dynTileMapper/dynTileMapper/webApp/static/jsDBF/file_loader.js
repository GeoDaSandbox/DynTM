// todo: add support for IE.
// todo: return a "file-like" object with .read .seek .tell, etc;
//check for FIREFOX and Google Gears.
var FIREFOX = false;
var GEARS = false;
if (/Firefox[\/\s](\d+\.\d+)/.test(navigator.userAgent)){ //test for Firefox/x.x or Firefox x.x
    var ffversion=new Number(RegExp.$1) // capture x.x portion and store as a number
    if (ffversion>=3){
        FIREFOX = true;
    }
} else if (!window.google || !google.gears) {
    var msg = "The GeoDa Center takes advantage of Google Gears to enable " + 
          "advanced functionality in our line of web applications.  " +
          "Please install Google Gears!";
    location.href = "http://gears.google.com/?action=install&message=" + msg +
            "&return=http://localhost/~charlie/";
} else {
    GEARS = true;
}



function subclass(constructor, superConstructor)
{ // from: http://www.golimojo.com/etc/js-subclass.html
    function surrogateConstructor()
    {
    }

    surrogateConstructor.prototype = superConstructor.prototype;

    var prototypeObject = new surrogateConstructor();
    prototypeObject.constructor = constructor;

    constructor.prototype = prototypeObject;
}


// The File Class.
function File(data)
{
    this.data = data;
    this.pos = 0;
}
File.prototype.read = function(n_bytes){
    //return n bytes
    start = this.pos;
    this.pos+=n_bytes;
    return this.data.slice(start,this.pos);
}
File.prototype.skip = function(n_bytes){
   this.pos += n_bytes;
}
File.prototype.seek = function(n_bytes){
    this.pos = n_bytes;
}
File.prototype.tell = function(){
    return this.pos;
}
subclass(GearsFile,File);
function GearsFile(data)
{
    File.call(this,data);
}
GearsFile.prototype.read = function(n_bytes){
    var n = n_bytes;
    blob = this.data.blob;
    s = '';
    stop = Math.min(this.pos+n,blob.length);
    while (this.pos < stop){
        len = Math.min(n,1024); // max 1024 chunk size
        len = Math.min(blob.length-this.pos,len); // don't read off the end.
        ints = blob.getBytes(this.pos,len);
        for (var j in ints){
            s+=(String.fromCharCode(ints[j]));
        }
        this.pos += len;
        n-=len;
    }
    return s;
}
// The Opener Class.
function GCFileOpener(containerID,callback) { //GCFileOpener
    this.containerID = containerID;
    this.callback = callback;
    if (GEARS){
        this.gears_open();
    } else if (FIREFOX) {
        this.firefox_open();
    }
}
GCFileOpener.prototype.gears_open = function() {
    this.gears_file = '';
    var container = document.getElementById(this.containerID);
    form = "<form id='file_opener'>";
    form+= "<input id='file_opener_file' type='text'>";
    form+= "<input id='file_opener_browse' type='button' value='Browse'>";
    form+= "<input id='file_opener_open' type='button' value='Open'>";
    form+= "</form>";
    container.innerHTML += form;
    self = this;
    document.getElementById('file_opener_file').onclick = function(event){
        self.gears_onBrowse();
    };
    document.getElementById('file_opener_browse').onclick = function(event){
        self.gears_onBrowse();
    };
    document.getElementById('file_opener_open').onclick = function(event){
        self.gears_onOpen();
    };
}
GCFileOpener.prototype.gears_onBrowse = function() {
    var desktop = google.gears.factory.create('beta.desktop');
    self=this;
    gears_callback = function(files){
        if (files.length > 0){
            self.gears_onSelect(files);
        }
    };
    desktop.openFiles(gears_callback,{singleFile:true});
}
GCFileOpener.prototype.gears_onSelect = function(files) {
    file = files[0]
    this.gears_file = file;
    document.getElementById('file_opener_file').value = file.name;
}
GCFileOpener.prototype.gears_onOpen = function() {
    if (this.gears_file){
        this.callback(new GearsFile(this.gears_file));
    }
}
GCFileOpener.prototype.firefox_open = function() {
    var container = document.getElementById(this.containerID);
    form = "<form id='file_opener'>";
    form+= "<input id='file_opener_file' type='file'>";
    form+= "<input id='file_opener_open' type='button' value='Open'>";
    form+= "</form>";
    container.innerHTML += form;
    self = this;
    document.getElementById('file_opener_open').onclick = function(event){
        self.firefox_onOpen();
    };
}
GCFileOpener.prototype.firefox_onOpen = function(e) {
    file_field = document.getElementById('file_opener_file');
    file = file_field.files[0];
    if (file){
        //myfile = new File(file.getAsBinary());
        //alert(myfile.read(100));
        this.callback(new File(file.getAsBinary()));
    }
}

