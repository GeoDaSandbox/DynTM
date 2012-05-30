import pyGWS
DEBUG = False

class GeoDaWS_Dict(pyGWS.GeoDaWebServiceClient):
    #_url="http://apps.geodacenter.org/dict.json/"
    _url="http://127.0.0.1:8000/dict.json/"
    def __init__(self,AccessKeyID, AccessKey):
        pyGWS.GeoDaWebServiceClient.__init__(self,AccessKeyID,AccessKey)
    def __getitem__(self,key):
        result = self._open(key).read()
        return eval(result,{},{})['value']
    def __setitem__(self,key,value):
        data = {"value":value}
        result = self._open(key,data).read()
        if DEBUG: print result
    def keys(self):
        result = self._open('KEYS').read()
        return eval(result,{},{})
    def values(self):
        result = self._open('VALUES').read()
        return eval(result,{},{})

if __name__ == '__main__':
    AccessKeyID = '1'
    AccessKey = 'shared_secret'

    c = GeoDaWS_Dict(AccessKeyID=AccessKeyID,AccessKey=AccessKey)

    ### Set a bunch of keys
    print "Setting Keys..."
    c['test_api'] = 'a value set by the apiuser!'
    c['a'] = 5
    c['b'] = 7
    c['my name'] = 'charlie'
    c['a really long key name'] = 'short val'
    c['c'] = """A Really Long Value
with multiple
lines

Should,
work,
ok."""

    print "Reading Keys..."
    print c['test_api']
    print c['a']
    print c['b']
    print c['my name']

    print c['a really long key name']
    print c['c']
    c['c'] = 0
    print c['c']

    for i in range(1,10):
        c['i%d'%i] = i
        print c['i%d'%i]
