from django.contrib import auth

class GWS_UserMiddleware(object):
    def process_request(self,request):
        if 'HTTP_AUTHORIZATION' in request.META:
            user = auth.authenticate(request=request)
            if user:
                request.user = user
                auth.login(request,user)
        return
