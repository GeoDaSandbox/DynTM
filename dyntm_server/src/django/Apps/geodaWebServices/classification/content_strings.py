content_strings = {}
content_strings["client.js"] = """/* GeoDaCenter Web Services -- Classification Client API
 *
 *  Author: Charles.R.Schmidt@asu.edu
 *  Version: 0.0.1
 *
 *  Notes: This Client API Enables Cross-Orgin acces the the GWS Classification Service.
 *         This script will load a hidden iFrame and communicate with it through
 *         javascript's postMessage API which allows cross origin communication.
*/
function ClassificationService(){
    this.SERVICEADDRESS= "http://SERVERADDRESS/classifier/service.html";
    this.DEFAULT_K = 5
    this.count = 0;
    this.iframe = document.createElement('iframe');
    this.iframe.src = this.SERVICEADDRESS;
    this.iframe.width = "0px";
    this.iframe.height = "0px";
    this._callbacks = {};
    this.iframe.style.display = "none";
    this.iframe.style.visibility = "hidden";
    document.body.appendChild(this.iframe);
    var that = this;
    window.addEventListener("message",function(evt){that.receiveMessage(evt);},false);
}

// METHOD HELPER FUNCTIONS
ClassificationService.prototype.Quantiles = function(y,callBack,k){
    return this._classify(y,callBack,"quantile",k);
}
ClassificationService.prototype.Percentiles = function(y,callBack,k){
    return this._classify(y,callBack,"percentile",k);
}
ClassificationService.prototype.Box_Plot = function(y,callBack,k){
    return this._classify(y,callBack,"boxmap",k);
}
ClassificationService.prototype.Equal_Interval = function(y,callBack,k){
    return this._classify(y,callBack,"equalinterval",k);
}
ClassificationService.prototype.Natural_Breaks = function(y,callBack,k){
    return this._classify(y,callBack,"naturalbreak",k);
}
ClassificationService.prototype.Natural_Breaks_Full = function(y,callBack,k){
    return this._classify(y,callBack,"naturalbreak_full",k);
}
ClassificationService.prototype.Std_Mean = function(y,callBack,k){
    return this._classify(y,callBack,"stddev",k);
}
ClassificationService.prototype.Category = function(y,callBack,k){
    return this._classify(y,callBack,"Category",k);
}

// Private classify method is called by helper methods.
ClassificationService.prototype._classify = function(y,callBack,method,k){
    // _classify
    //
    // Arguments:
    //      y (list), Values to be classified.
    //      callBack (function), called with the resulting classifcaiton object.
    //      method (string), The classification method (see helper functions.)
    //      k (int), Number of classes.
    //
    // Returns:
    //      reqID (string), Request Identifier,
    //
    // Side Effects:
    //      Will call the callBack function with the final classification object.
    //
    if (k) { this.k = k; } else { this.k = this.DEFAULT_K;}
    var requestTime = new Date().getTime();
    // MESSAGE:  requestTime:method:k:y
    var requestID = requestTime+":"+method+":"+k;
    msg = requestID+":"+y.join(',');
    this._callbacks[requestID] = callBack;
    this.iframe.contentWindow.postMessage(msg,"*");
    return requestID;
}

ClassificationService.prototype.receiveMessage = function(event){
    if (event.data.slice(0,8)=="gwscl://"){
        var msg = event.data.slice(8);
        var reqID,cl;
        reqID = msg.split("|||")[0];
        cl = JSON.parse(msg.split("|||")[1]);
        this._callbacks[reqID](cl);
    }
}


// TESTS AND TEST HELPERS ARE BELOW, can be removed.

ClassificationService.prototype.test_Equal_Interval = function(){
    var list;
    y = [5,10,20,1,3,3,4,5,6,99,100];
    yb = [2,2,2,2,2,2,2,2,2,6,6];
    this.Equal_Interval(y,function(data){
        if (list_compare(data["id2colorclass"].split(','),yb)){
            alert("test_Equal_Interval: PASS");
        } else {
            alert("test_Equal_Interval: FAIL");
            alert(data["id2colorclass"]);
            alert(yb);
        }
    } ,5);
}

function list_compare(l1,l2){
    if (l1.length != l2.length){
        return false;
    }   
    for (var i=0; i<l1.length; i++){
        if (l1[i]!=l2[i]) return false;
    }   
    return true;
}

"""

content_strings["service.html"] = """<html>
<head>
<script src="http://code.jquery.com/jquery-1.4.2.min.js"></script>
<script>
function ClassificationServerEnd(){
    this.SERVICE_URL = "http://SERVERADDRESS/classifier?";
    this.requests = {};
    var that = this;
    window.addEventListener("message",function(event){that.receiveMessage(event);},false);
}
ClassificationServerEnd.prototype.receiveMessage = function(event){
    //alert(event.origin);
    //alert(event.source);
    //alert(event.data);
    var message = event.data.split(":");
    var reqTime, method, k, y;
    reqTime = message[0];
    method = message[1];
    k = message[2];
    var reqID = reqTime+":"+method+":"+k;
    y = message[3];
    var size = y.split(',').length;
    //event.source.postMessage("I got request ("+reqID+") with"+size+" elements!","*");
    var reqData = {METHOD:method, VALUES:y, NOCLS:k};
    var that = this;
    $.post("http://SERVERADDRESS/classifier?",reqData,function(data,txtStatus){
                that.receiveClassification(data,txtStatus,event,reqID);
            },"JSON");
}
ClassificationServerEnd.prototype.receiveClassification = function(data,txtStatus,event,reqID){
    event.source.postMessage("gwscl://"+reqID+"|||"+data,"*");
    
}
var service = new ClassificationServerEnd();
</script> </head>
<body>
This window provides cross origin access to the GeoDaCenter's Classifcation Web Service.<br>
This page should not be accessed directly, but instead of loaded via the JavaScript API located here,<br>
http://127.0.0.1:8000/classifier.js<br>
<br>
This is a hidden window.
</body></html>
"""

