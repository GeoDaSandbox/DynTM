from django.utils import simplejson
import pyGWS
import array
UNSIGNED_ITEM_TYPES = {array.array('B').itemsize:'B', array.array('H').itemsize:'H', array.array('I').itemsize:'I', array.array('L').itemsize:'L'}
import zlib,base64
import urllib
import time
import math
import hashlib
DEBUG = False
LARGE_FILE_SIZE = 50*1024*1024
CHUNK_SIZE = 5*1024*1024
class GeoDaWS_DynTM(pyGWS.GeoDaWebServiceClient):
    """
    Python Client for the Dynamic Tile Mapper Web Service.

    Example Usage:
    
    Open a connection...
    >>> AccessKeyID = 'testuser4c3e5149'
    >>> AccessKey = '753b191f8ba15595361c962899b90d009accee6a'
    >>> client = GeoDaWS_DynTM(AccessKeyID=AccessKeyID,AccessKey=AccessKey)

    Upload a new Shapefile...
    >>> shp = open("../../../example_data/stl_hom/stl_hom.shp",'rb')
    >>> shx = open("../../../example_data/stl_hom/stl_hom.shx",'rb')
    >>> result = client.createTileSet(shp,shx)
    >>> result == 'testuser:B9C118EB30A9EAE19C93902E9F01EF8A'
    True
    >>> time.sleep(0.5)

    Describe the New Shapefile....
    >>> result = client.describeTileSet('testuser:B9C118EB30A9EAE19C93902E9F01EF8A')['shpfile']
    >>> result == 'B9C118EB30A9EAE19C93902E9F01EF8A'
    True
    >>> time.sleep(0.5)

    Download a tile...
    >>> png = client.getTile('testuser:B9C118EB30A9EAE19C93902E9F01EF8A',5,7,12)
    >>> png[:4] == '\x89PNG'
    True
    >>> open('tst0.png','wb').write(png)

    Post a Classification...
    >>> cl = [3, 2, 2, 3, 2, 3, 2, 3, 3, 3, 3, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 2, 2, 3, 3, 3, 3, 2, 2, 2, 2, 3, 3, 2, 2, 2, 2, 3, 2, 3, 3, 2, 2, 2, 3, 3, 3, 2, 2, 2, 3, 3, 3, 2, 2, 2, 2, 2, 2, 3, 3, 3, 2, 2, 2, 2, 3, 3, 2, 2, 3, 3, 3, 2, 2]
    >>> result = client.createClassification('testuser:B9C118EB30A9EAE19C93902E9F01EF8A',cl)
    >>> result == 'testuser:474f117491ba503bde2b1eb2b9a36b3a'
    True
    >>> time.sleep(0.5)

    List Classifications...
    >>> result = client.listClassifications()
    >>> 'testuser:474f117491ba503bde2b1eb2b9a36b3a' in result
    True
    >>> time.sleep(0.5)

    Download a classified tile...
    >>> png = client.getTile('testuser:B9C118EB30A9EAE19C93902E9F01EF8A',5,7,12,'testuser:474f117491ba503bde2b1eb2b9a36b3a')
    >>> png[:4] == '\x89PNG'
    True
    >>> open('tst1.png','wb').write(png)

    Upload a colorScheme...
    >>> colors = ['#00ff00','#0000ff']
    >>> result = client.createColorScheme(colors)
    >>> result == 'testuser:b0726a29f9068870b701650e7adae8f7'
    True
    >>> time.sleep(0.5)

    Download a classified colored tile...
    >>> png = client.getTile('testuser:B9C118EB30A9EAE19C93902E9F01EF8A',5,7,12,'testuser:474f117491ba503bde2b1eb2b9a36b3a','testuser:b0726a29f9068870b701650e7adae8f7')
    >>> png[:4] == '\x89PNG'
    True
    >>> open('tst2.png','wb').write(png)

    Delete a Classification...
    >>> client.deleteClassification('testuser:474f117491ba503bde2b1eb2b9a36b3a')
    True

    Delete a ColorSchme...
    >>> client.deleteColorScheme('testuser:b0726a29f9068870b701650e7adae8f7')
    True

    Delete a shapefile...
    >>> client.deleteTileSet('testuser:B9C118EB30A9EAE19C93902E9F01EF8A')
    True
    >>> time.sleep(0.5)
    >>> result = client.describeTileSet('testuser:B9C118EB30A9EAE19C93902E9F01EF8A')
    >>> result == {'error': 'TileSet Not Found'}
    True


    """
    _url="http://apps2.geodacenter.org/dyntm.json/"
    #_url="http://apps2.geodacenter.org/dyntm.json/"
    #_url="http://127.0.0.1:8000/dyntm.json/"
    def __init__(self,AccessKeyID, AccessKey):
        pyGWS.GeoDaWebServiceClient.__init__(self,AccessKeyID,AccessKey)
    def createTileSet(self,shpfile,shxfile):
        """
        Post a new TileSet to the server.
        
        Parameters:
        shpfile -- an open file-like object containing the ".shp" file.
        shxfile -- an open file-like object containing the ".shx" file.

        Returns:
        tileSetID of the newly create TileSet if successful, otherwise false.

        Example:
        >>> AccessKeyID = 'testuser4c3e5149'
        >>> AccessKey = '753b191f8ba15595361c962899b90d009accee6a'
        >>> client = GeoDaWS_DynTM(AccessKeyID=AccessKeyID,AccessKey=AccessKey)
        >>> shp = open("../../../example_data/stl_hom/stl_hom.shp",'rb')
        >>> shx = open("../../../example_data/stl_hom/stl_hom.shx",'rb')
        >>> result = client.createTileSet(shp,shx)
        >>> result == 'testuser:B9C118EB30A9EAE19C93902E9F01EF8A'
        True
        >>> time.sleep(0.5)
        >>> client.deleteTileSet('testuser:B9C118EB30A9EAE19C93902E9F01EF8A')
        True
        """
        shpfile.seek(0,2)#EOF
        f_size = shpfile.tell()
        shpfile.seek(0)
        if f_size > (LARGE_FILE_SIZE):
            print "Large File: Uploading in parts..."
            return self.createTileSet_Chunks(shpfile,shxfile,f_size)
        data = {}
        #data['shpname'] = 'stl_hom'
        data['shp'] = base64.b64encode(zlib.compress(shpfile.read()))
        data['shx'] = base64.b64encode(zlib.compress(shxfile.read()))
        #data['dbf'] = base64.b64encode(zlib.compress(dbf.read()))
        url = self._post('tileset',data,raiseErrors=False)
        if url.code == 200:
            return simplejson.loads(url.read())['TileSetID']
        else:
            print "Server returned error code: %d"%(url.code)
            return url
    def createTileSet_Chunks(self,shpfile,shxfile,shp_size):
        """
        Post a new TileSet to the server, by uploading the file in chunks.
        We'll use a multipart upload inspired by S3's new multipart upload feature.

        Parameters:
        shpfile -- an open file-like object containing the ".shp" file.
        shxfile -- an open file-like object containing the ".shx" file.

        Returns:
        tileSetID of the newly create TileSet if successful, otherwise false.
        """
        #calc MD5
        shpMD5 = hashlib.md5()
        dat = shpfile.read(2**16)
        while dat:
            shpMD5.update(dat)
            dat = shpfile.read(2**16)
        shpfile.seek(0)

        #initiate upload
        data = {}
        data['shpmd5'] = shpMD5.hexdigest().upper()
        data['shx'] = base64.b64encode(zlib.compress(shxfile.read()))
        url = self._post('tileset',data,raiseErrors=False)
        if url.code == 200:
            result = simplejson.loads(url.read())
            if 'uploadId' in result:
                print "Large File: Initializing Upload, MD5=",data['shpmd5']
                del data['shx']
                parts = []
                data['uploadId'] = result['uploadId']
                data['partNum'] = 1
                data['shpPart'] = base64.b64encode(zlib.compress(shpfile.read(CHUNK_SIZE)))
                while data['shpPart']:
                    try:
                        t0 = time.time()
                        url = self._post('tileset',data,raiseErrors=False)
                        result = url.read()
                        result = simplejson.loads(result)
                        t1 = time.time()
                        if result['etag']:
                            kbps = ((len(data['shpPart'])/1024.0)/(t1-t0))
                            print "Large File: Uploaded Part %d (%s): %0.2f kB/s"%(data['partNum'],result['etag'],kbps)
                            parts.append(result['etag'])
                            data['partNum']+=1
                            dat = shpfile.read(CHUNK_SIZE)
                            if dat:
                                data['shpPart'] = base64.b64encode(zlib.compress(dat))
                            else:
                                data['shpPart'] = ''
                        else:
                            "Part %d upload failed. Trying Again."%data['partNum']
                    except:
                        raise
                del data['shpPart']
                del data['partNum']
                data['partsList'] = ','.join(parts)
                url = self._post('tileset',data,raiseErrors=False)
                if url.code == 200:
                    print "Large File: Upload Complete"
                    return simplejson.loads(url.read())['TileSetID']
                else:
                    print "Server returned error code: %d"%(url.code)
                    return url
            else:
                if "TileSetID" in result:
                    print "Large File: Already Exists on Server, No Upload needed."
                    return result['TileSetID']
        else:
            print "Server returned error code: %d"%(url.code)
            return url
            
    def listTileSets(self):
        result = self._get('tileset',raiseErrors=False)
        if result.code == 200:
            return eval(result.read(),{},{})['tilesets']
        else:
            return None
    def describeTileSet(self,tileSetName):
        result = self._get('tileset/%s'%tileSetName).read()
        return simplejson.loads(result)
    def deleteTileSet(self,tileSetName):
        result = self._delete('tileset/%s'%tileSetName).read()
        return simplejson.loads(result)
    @staticmethod
    def getTile(tileSetID,zoom,x,y,clid=None,csid=None,border=True):
        """
        Method for retrieving tiles, does not require Authentication and can be called without instantiation.
        Example:
        >>> png = GeoDaWS_DynTM.getTile('testuser:B9C118EB30A9EAE19C93902E9F01EF8A',5,7,12)
        """
        cls = pyGWS.GeoDaWebServiceClient()
        cls._url = "http://apps2.geodacenter.org/dyntm/t"
        #cls._url = "http://apps2.geodacenter.org/dyntm/t"
        #cls._url = "http://127.0.0.1:8000/dyntm/t"
        req = '?ts=%s&z=%s&x=%s&y=%s'%(tileSetID,zoom,x,y)
        if not border:
            req+='&b=0'
        if clid:
            req+='&cl=%s'%(clid)
        if csid:
            req+='&cs=%s'%(csid)
        result = cls._get(req)
        if result.code == 200:
            return result.read()
        else:
            return result
    def listClassifications(self):
        result = self._get('cl',raiseErrors=False)
        if result.code == 200:
            return simplejson.loads(result.read())['classifications']
        else:
            return None
    def deleteClassification(self,clid):
        result = self._delete('cl/%s'%clid)
        return simplejson.loads(result.read())
    def createClassification(self,tileSetID,classes):
        a = array.array(UNSIGNED_ITEM_TYPES[1])
        a.fromlist(classes)
        a = base64.b64encode(zlib.compress(a.tostring()))
        data = {'dat':a,'tsid':tileSetID,'format':'b64zlib'}
        url = self._post('cl',data,raiseErrors=False)
        if url.code == 200:
            return simplejson.loads(url.read())['ClassificationID']
        else:
            return url
    def createClassification2(self,tileSetID,classes):
        a = ','.join(map(str,classes))
        data = {'dat':a,'tsid':tileSetID,'format':'csv'}
        url = self._post('cl',data,raiseErrors=False)
        if url.code == 200:
            return simplejson.loads(url.read())['ClassificationID']
        else:
            return url
    def getClassification(self,clid):
        result = self._get('cl/%s'%clid)
        if result.code == 200:
            return simplejson.loads(result.read())
        else:
            return result
    def listColorSchemes(self):
        result = self._get('colors',raiseErrors=False)
        if result.code == 200:
            return simplejson.loads(result.read())['colorschemes']
        else:
            return None
    def deleteColorScheme(self,csid):
        result = self._delete('colors/%s'%csid)
        return simplejson.loads(result.read())
    def createColorScheme(self,colors,background_color='#000001',border_color='#000000'):
        """
        colors -- list of strings
                Each color should be in HEX RGB format beginning with a '#'.
                The first color in the list provided is assigned to class 2, the next to class 3 and so on.

                Class 0 and Class 1 are reserved for the background and borders respectivly.
                The Background color should NOT be used anywhere else in the color scheme.
                    Since this color will be made transparent.

        Example:
        colors = ['#ff0000','#00ff00','#0000ff']
        client.createColorScheme(colors)
        """
        data = {'colors':','.join(colors)}
        data['background'] = background_color
        data['borders'] = border_color
        result = self._post('colors',data,raiseErrors=False)
        if result.code == 200:
            return simplejson.loads(result.read())['ColorSchemeID']
        else:
            return result
    def getColorScheme(self,csid):
        result = self._get('colors/%s'%csid).read()
        return simplejson.loads(result)
if __name__ == '__main__':
    # When running the django development server, importing simplejson causes the server to reload.
    # This causes the tests to fail because the server isn't available.
    # Sleeping for 2 seconds allows the server to finish reloading.
    # Another option to to run the dev server with the '--noreload' option.
    # This was discovered after many hours of debugging.
    import time
    time.sleep(3)
    import doctest
    #doctest.testmod()

    ### More testing
    AccessKeyID = 'testuser4c3e5149'
    AccessKey = '753b191f8ba15595361c962899b90d009accee6a'
    client = GeoDaWS_DynTM(AccessKeyID=AccessKeyID,AccessKey=AccessKey)
    #shp = open("/Users/charlie/Documents/Work/NIH/ASU_Data_dbase/shps/ntracts.shp",'rb')
    #shx = open("/Users/charlie/Documents/Work/NIH/ASU_Data_dbase/shps/ntracts.shx",'rb')
    #shp = open("/Users/charlie/Documents/data/usa/usa.shp","rb")
    #shx = open("/Users/charlie/Documents/data/usa/usa.shx","rb")
    #shp = open("../../../example_data/stl_hom/stl_hom.shp",'rb')
    #shx = open("../../../example_data/stl_hom/stl_hom.shx",'rb')
    shp = open("/Users/charlie/Documents/Work/NIJ/Target1/Mesa Data/Mesa_Beats/Beats_WGS84.shp",'rb')
    shx = open("/Users/charlie/Documents/Work/NIJ/Target1/Mesa Data/Mesa_Beats/Beats_WGS84.shx",'rb')
    print "posting:"
    resp = client.createTileSet(shp,shx)
    print resp

    #cl = [3, 2, 2, 3, 2, 3, 2, 3, 3, 3, 3, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 2, 2, 3, 3, 3, 3, 2, 2, 2, 2, 3, 3, 2, 2, 2, 2, 3, 2, 3, 3, 2, 2, 2, 3, 3, 3, 2, 2, 2, 3, 3, 3, 2, 2, 2, 2, 2, 2, 3, 3, 3, 2, 2, 2, 2, 3, 3, 2, 2, 3, 3, 3, 2, 2]
    #print "posting:", client.createClassification('testuser:B9C118EB30A9EAE19C93902E9F01EF8A',cl)
    #colors = ['#00ff00','#0000ff']
    #print "posting:", client.createColorScheme(colors)
