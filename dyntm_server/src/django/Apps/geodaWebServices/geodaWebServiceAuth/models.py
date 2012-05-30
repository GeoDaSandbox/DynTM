if __name__=='__main__':
    import sys,os
    sys.path.append('/Users/charlie/Documents/repos/geodacenter/geodaWeb/trunk/django/Projects')
    os.environ['DJANGO_SETTINGS_MODULE']='gws_sqlite.settings'
# Built-in Imports
import time, base64, hmac, hashlib
import random
import urllib
from wsgiref.handlers import format_date_time
import logging
logger = logging.getLogger("gws")
#Django Imports
from django.contrib.auth.models import User,get_hexdigest,check_password
#Custom Imports
from gws_lib import db
#from django.db import models
#from django.contrib import admin
# Charecters to be used in ker generator, picked to be not confusing, no i,l,1,',", etc.
#SPECIAL_CHARS = '!#$&*+,-.:;<=>?@~[]^_'
#CHARS = '023456789ABCDEFGHJKLMNOPQRSTUVWXYZabcdefghjkmnopqrstuvwxyz'

class GWS_User(db.Model):
    """
    User model to store via gws_lib.
    """
    username = db.StringProperty() #required
    password = db.StringProperty() #required
    first_name = db.StringProperty() #optional
    last_name = db.StringProperty() #optional
    email = db.StringProperty() #optional
    is_staff = db.BooleanProperty() #required
    is_superuser = db.BooleanProperty() #required
    def set_password(self,raw_password):
        """
        copied from django.contrib.auth.models
        """
        import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)
    def check_password(self,raw_password):
        """
        not backwards compatible.
        """
        return check_password(raw_password,self.password)
    @property
    def User(self):
        """Returns a Django User Object"""
        user,created = User.objects.get_or_create(username=self.username)
        if created:
            user = self.configure_user(user)
        return user
    def configure_user(self,user):
        user.password = self.password
        user.first_name = self.first_name
        user.last_name = self.last_name
        user.email = self.email
        user.is_staff = self.is_staff
        user.is_superuser = self.is_superuser
        user.save()
        return user
    
class GWS_AccessKey(db.Model):
    """
    The AccessKey is used to access a WebService API via Signed Requests
    Each access key is associated with a user.

    Correctly signing a request with an access key, will grant the request the same permissions as the user associated with the key.

    Multiple Keys can be associated with a given user, this allows the user to cycle keys in and out of service.

    The key_name for this model is the accessKeyID and must be set to username+'%x'%time.mktime(time.gmtime()) on creation.
    """
    user = db.ReferenceProperty(GWS_User)
    #accessKeyID = db.StringProperty()
    accessKey = db.StringProperty() #This is the Shared Secert
    def calc_signature(self,request):
        string2sign = string_to_sign(request)
        signature = base64.b64encode(hmac.new(self.accessKey.encode('UTF-8'),string2sign,hashlib.sha1).hexdigest())
        return signature
    @property
    def User(self):
        user = GWS_User.get(self.user)
        return user.User
def string_to_sign(request):
    """ Returns the 'string2sign' based on a Django Request object 

    To compare againts the Authorization Header such as,
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
    verb = request.method # HTTP-Verb
    if request.raw_post_data:
        cmd5 = hashlib.md5(request.raw_post_data).hexdigest()
    else:
        cmd5 = ''
    #cmd5 = request.META.get('HTTP_CONTENT_MD5','')
    #assert cmd5 == request.META.get('HTTP_CONTENT_MD5','')
    ctype = request.META.get('CONTENT_TYPE','')
    date = request.META.get('HTTP_DATE','')
    path = urllib.quote(request.get_full_path())

    string2sign = "%s\n%s\n%s\n%s\n%s"%(verb,cmd5,ctype,date,path)
    string2sign = string2sign.encode('UTF-8') # ASCII
    return string2sign
def create_gws_user(username,password,first_name='',last_name='',email='',staff=False,superuser=False):
    if GWS_User.get(username):
        raise ValueError, "Username already exists"
    else:
        user = GWS_User(username)
        user.username = username
        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.is_staff = staff
        user.is_superuser = superuser
        user.put()
        for i in range(5): #make sure database is consistent.
            u = GWS_User.get(username)
            if not u:
                continue
            elif u.check_password(password):
                break
            else: #user exists but passwords don't match.
                raise ValueError, "Username already taken"
        logger.info("GWS: created GWS_User(%s)"%username)
        return user

def create_accesskey(user):
    keyid = '%s%x'%(user.username,time.mktime(time.gmtime()))
    key = GWS_AccessKey(keyid)
    key.accessKey = get_hexdigest('sha1', str(random.random()), str(random.random()))
    key.user = user.username
    key.put()
    logger.info("GWS: created GWS_AccessKey for user: %s"%user.username)
    return key


#class AccessKey(models.Model):
#    """
#    The AccessKey is used to access a WebService API via Signed Requests
#    Each access key is associated with a user.
#
#    Correctly signing a request with an access key, will grant the request the same permissions as the user associated with the key.
#
#    Multiple Keys can be associated with a given user, this allows the user to cycle keys in and out of service.
#    """
#    user = models.ForeignKey(User)
#    accessKeyID = models.AutoField(primary_key=True)
#    accessKey = models.CharField(max_length=100) #This is the Shared Secert
#    def calc_signature(self,request):
#        string2sign = string_to_sign(request)
#        signature = base64.b64encode(hmac.new(self.accessKey.encode('UTF-8'),string2sign,hashlib.sha1).hexdigest())
#        return signature
#admin.site.register(AccessKey)

#def key_generator():
#    """ Return a randomized secert key
#    DEPRECATED instead use:
#    get_hexdigest('sha1', str(random.random()), str(random.random()))
#    """
#    raise DeprecationWarning,"This is deprecated"
#    rng = random.Random()
#    p = rng.sample(CHARS,50) + rng.sample(SPECIAL_CHARS,2)
#    rng.shuffle(p)
#    p = ''.join(p)
#    return p
