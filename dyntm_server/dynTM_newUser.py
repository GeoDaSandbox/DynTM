import sys, os
sys.path.append('/usr/local/django')
os.environ['DJANGO_SETTINGS_MODULE']='gws_sqlite.settings'

from geodaWebServices.geodaWebServiceAuth import models

passwd = filter(lambda x:str.isalnum(x), os.urandom(999))
user = models.create_gws_user('dtmUser',passwd)
key = models.create_accesskey(user)

print "Access Key ID:", key.key_name
print "Access Key:", key.accessKey