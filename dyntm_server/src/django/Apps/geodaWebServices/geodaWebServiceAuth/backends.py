import logging
logger = logging.getLogger("gws")
from django.contrib.auth.models import check_password
from django.contrib.auth.backends import ModelBackend
from models import GWS_User,GWS_AccessKey

class GWSUserBackend(ModelBackend):
    """ Authenticate against GWS_User models stored via gws_lib """
    def authenticate(self, username=None, password=None, request=None):
        if username and password:
            return self.auth_user(username,password)
        elif request:
            return self.auth_key(request)
    def auth_user(self, username, password):
        user = GWS_User.get(username)
        if user and user.check_password(password):
            u = user.User
            return user.User
    def auth_key(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2 and auth[0] == 'GeoDaWS':
                AccessKeyID,signature = auth[1].split(':')
                accesskey = GWS_AccessKey.get(AccessKeyID)
                if accesskey and accesskey.calc_signature(request) == signature:
                    return accesskey.User
                else:
                    return None
