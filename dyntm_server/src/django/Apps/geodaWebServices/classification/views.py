# Setup Django for testing outside a server environment.
if __name__=='__main__':
    import sys,os
    sys.path.append('/Users/charlie/Documents/repos/geodacenter/geodaWeb/trunk/django/Projects')
    os.environ['DJANGO_SETTINGS_MODULE']='gws_sqlite.settings'

# Built-in Imports
import logging
import zlib, base64
import hashlib
import array
import sys
# Django Imports
from django.template import Template
# Custom Imports
from geodaWebServices import WebService
# 3rd Party Imports
from pysal.esda import mapclassify
import numpy
# LOCAL Imports
from content_strings import content_strings

logging.basicConfig(filename='/var/log/dtm.log',level=logging.INFO)
logger = logging.getLogger("gws.classificationService")

CLASSIFICATION_METHODS = {'quantile':mapclassify.Quantiles, 
            'percentile':mapclassify.Percentiles, 
            'boxmap':mapclassify.Box_Plot,
            'equalinterval':mapclassify.Equal_Interval,
            'naturalbreak_full':mapclassify.Natural_Breaks,
            'naturalbreak':mapclassify.Jenks_Caspall_Sampled,
            'stddev':mapclassify.Std_Mean,
            'Category':mapclassify.User_Defined}
NO_ARGS = ['percentile','boxmap','stddev']

class JavaScriptClient(WebService):
    def __init__(self,format='JS',auth=False):
        WebService.__init__(self,format,auth_required=auth)
    def get(self):
        return self.write(content_strings['client.js'].replace("SERVERADDRESS",self.request.META["HTTP_HOST"]))
        #return self.write("alert('JavaScript Classification Client: HERE');")
class JavaScriptService(WebService):
    def __init__(self,format='HTML',auth=False):
        WebService.__init__(self,format,auth_required=auth)
    def get(self):
        return self.write(content_strings['service.html'].replace("SERVERADDRESS",self.request.META["HTTP_HOST"]))
        #return self.write("<html><body>JavaScript Classification Service: HERE</body></html>");
class ClassificationHandler(WebService):
    def __init__(self,format='JSON',auth=False):
        t = Template("<html><head><title>DynTM</title></head><body>{{body}}</body></html>")
        WebService.__init__(self,format,t,auth_required=auth)
    def get(self):
        try:
            return self.run()
        except:
            raise
            return self.write({"status":"failed"})
    def post(self):
        try:
            return self.run()
        except:
            raise
            return self.write({"status":"failed"})
    def parse_request(self):
        REQ = self.request.REQUEST
        required_items = [REQ.get(k,False) for k in ['METHOD','VALUES','NOCLS']]
        if False in required_items:
            return False
        meth,values,nocls = required_items
        logger.debug("Method: %s"%meth)
        if meth not in CLASSIFICATION_METHODS:
            return False
        if REQ.get("b64encode",False) == "True":
            logger.debug("Values are Base64")
            dat = base64.b64decode(values)
            typ = dat[0]
            a = array.array(typ)
            a.fromstring(dat[1:])
            if sys.byteorder == 'big':
                a.byteswap()
            values = numpy.array(a)
            b64 = True
        else:
            logger.debug("Values are CSV")
            values = values.split(',')
            values = numpy.array(map(float,values))
            b64 = False
        nocls = int(nocls)
        return meth,values,nocls,b64
    def classify(self,method,values,nocls,b64=False):
        if method == 'Category':
            l = list(set(values))
            logger.info(l)
            l.sort()
            logger.info(l)
            cat2cls = dict([(j,i+2) for i,j in enumerate(l)])
            logger.info(cat2cls)
            yb = ','.join(map(str,[cat2cls[v] for v in values]))
            k = len(l)
            if k > 250:
                return {"status":"failed","message":"The classification method you choose is not appropriate for this variable."}
            label = ','.join(["%0.2f -- %0.2f"%(a,b) for a,b in zip(l,l)])
            logger.info(label)
        else:
            if method in NO_ARGS:
                try:
                    c = CLASSIFICATION_METHODS[method](values)
                except:
                    logger.info(values)
                    return {"status":"failed"}
            else:
                try:
                    c = CLASSIFICATION_METHODS[method](values,nocls)
                except:
                    logger.info(values)
                    logger.info(nocls)
                    logger.info(method)
                    logger.exception("Something awful happened!")
                    return {"status":"failed"}
            try:
                yb = [x[0] for x in c.yb]
            except:
                yb = c.yb
            yb = ','.join(map(str,[x+2 for x in yb]))
            k = len(c.bins)
            lower = [min(values)]+list(c.bins)[:-1]
            label = ','.join(["%0.2f -- %0.2f"%(a,b) for a,b in zip(lower,c.bins)])
        if b64:
            vals = map(int,yb.split(','))
            a = array.array('B')
            a.fromlist(vals)
            if sys.byteorder == 'big':
                a.byteswap()
            yb = base64.b64encode(a.tostring())
        return {"status":"success","id2colorclass":yb,"breakpoint":label,"k":k}

    def run(self):
        result = self.parse_request()
        if not result:
            return self.write({"status":"failed"})
        meth,vals,nocls,b64 = result
        out = self.classify(meth,vals,nocls,b64)
        return self.write(out)
