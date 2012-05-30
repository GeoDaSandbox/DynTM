/* GeoDaCenter Web Services -- Classification Client API
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

