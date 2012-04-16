"""
pyGWS: Python clients for GeoDa Web Services

Author: Charles R Schmidt

Organization:
    The main package include general purpose utilities that are applicable to all GeoDa Web Services.
    Sub-packages contain the clients for individual web services.
"""
import urllib
import urllib2
from wsgiref.handlers import format_date_time
import time, base64, hmac, hashlib

DEBUG = False
class DeleteRequest(urllib2.Request):
    def get_method(self):
        return "DELETE"
class PutRequest(urllib2.Request):
    def get_method(self):
        return "PUT"

class GeoDaWebServiceClient(object):
    _url="http://127.0.0.1:8000"
    def __init__(self,AccessKeyID=None, AccessKey=None):
        if not AccessKeyID:
            self.__AccessKeyID = ''
            self.__AccessKey = ''
        else:
            self.__AccessKeyID = AccessKeyID
            self.__AccessKey = AccessKey
        while self._url.endswith('/'):
            self._url = self._url[:-1]
    def _get(self,path,raiseErrors=False):
        return self._open(path,raiseErrors=raiseErrors)
    def _post(self,path,data,raiseErrors=False):
        return self._open(path,data,raiseErrors=raiseErrors)
    def _put(self,path,data,raiseErrors=False):
        return self._open(path,data,raiseErrors=raiseErrors,Request=PutRequest)
    def _delete(self,path,raiseErrors=False):
        return self._open(path,raiseErrors=raiseErrors,Request=DeleteRequest)
    def _open(self,path,data=None,raiseErrors=False,Request=urllib2.Request):
        url = "%s/%s"%(self._url,path)
        r = Request(url)
        if data:
            r.add_data(urllib.urlencode(data))
        r = sign_request(r,self.__AccessKeyID,self.__AccessKey)
        if DEBUG: print r.get_header("Authorization")
        try:
            return urllib2.urlopen(r)
        except urllib2.HTTPError,e:
            if raiseErrors:
                raise
            else:
                return e
def sign_request(request,AccessKeyID,AccessKey,AuthType="GeoDaWS"):
    """ Signs a urllib2.Request and returns the signed Request Object

    Add the Authorization Header as such,
        Authorization: GeoDaWS AccessKeyID:Signature

    Signature = Base64( HMAC-SHA1( UTF-8-Encoding-Of( AccessKey,StringToSign ) ) )

    StringToSign =  HTTP-Verb + "\n" + 
                    Content-MD5 + "\n" +
                    Content-Type + "\n" +
                    Date + "\n" +
                    ResourceSelector

    ResourceSelector = "/path/to/resource"

    Example of StringToSign: "GET\n\ntext/plain\nThu, 01 Apr 2010 01:23:10 GMT\n/dict/user"

    Based on AWS REST Authentication: http://docs.amazonwebservices.com/AmazonS3/latest/index.html?RESTAuthentication.html
    """
    string2sign = "%(verb)s\n%(md5)s\n%(ctype)s\n%(date)s\n%(path)s"

    args = {'verb':'','md5':'','ctype':'','date':'','path':''}
    # HTTP-Verb
    args['verb'] = request.get_method() # HTTP-Verb
    # Content-MD5
    if not request.has_header('Content-md5') and request.has_data(): #Does not contain Content-MD5 header, but has data.
        md5 = hashlib.md5(request.get_data()).hexdigest() # Calc the data's MD5
        request.add_header('Content-md5',md5) # add the MD5 header
        args['md5'] = request.get_header('Content-md5')
    elif request.has_header('Content-md5'): #already has an md5 header
        args['md5'] = request.get_header('Content-md5')
    # Content-Type
    if not request.has_header("Content-type"):
        request.add_header("Content-type","text/plain")
    args['ctype'] = request.get_header("Content-type")
    # Date
    if not request.has_header("Date"):
        request.add_header("Date",format_date_time(time.time()))
    args['date'] = request.get_header('Date')
    # ResourceSelector
    args['path'] = urllib.quote(request.get_selector())

    if DEBUG: print "BEGIN STRING TO SIGN..."
    if DEBUG: print string2sign%args
    if DEBUG: print "END STRING TO SIGN."
    signature = base64.b64encode(hmac.new(AccessKey,(string2sign%args).encode('UTF-8'),hashlib.sha1).hexdigest())
    auth = "%s %s:%s"%(AuthType,AccessKeyID,signature)
    request.add_header('Authorization',auth)
    return request
