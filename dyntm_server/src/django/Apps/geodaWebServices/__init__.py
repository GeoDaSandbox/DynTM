from django.http import HttpResponse,HttpResponseNotFound,HttpResponseForbidden
from django.template import Context
from django.utils import simplejson
from django.contrib.auth import authenticate
from django.core.mail import mail_admins
import cStringIO

import geodaWebServiceAuth.models

class WebService:
    def __init__(self,format=None,default_template=None,auth_required=False):
        self.DISPATCH = {'GET':self.get,'POST':self.post,'DELETE':self.delete,'PUT':self.put}
        self.template = default_template
        self.format = format.lower()
        if self.format == 'json':
            self.write = self.render_json
        elif self.format == 'js':
            self.write = self.render_javascript
        elif self.format == 'png':
            self.write = self.render_png
        else:
            self.write = self.render
        self.auth_required = set()
        if auth_required and type(auth_required) == bool:
            #print "bool", auth_required
            self.auth_required = set(['GET','POST','PUT','DELETE'])
        elif auth_required and type(auth_required) == set:
            #print "set", auth_required
            self.auth_required = auth_required
        self.__unsigned_string = ''
    @classmethod
    def __profile_call__(cls,request,*args,**kwargs):
        import cProfile, pstats, time 
        prof = cProfile.Profile()
        prof = prof.runctx("globals()['r'] = cls.__real_call__(request,*args,**kwargs)", globals(), locals())
        stats = pstats.Stats(prof)
        stats.sort_stats("time")
        stats.stream = cStringIO.StringIO()
        stats.print_stats()
        stats.print_callers()
        #stats.dump_stats('/var/tmp/%f.dtm.profile'%(time.time()))
        #open('/var/tmp/%f.dtm.profile'%(time.time()),'w').write(stats.stream.getvalue())
        mail_admins("DTM Profile: %s"%request.get_full_path(),stats.stream.getvalue())
        return r
    @classmethod
    def __real_call__(cls,request,*args,**kwargs):
        self = cls()
        if request.method in self.auth_required and not request.user.is_authenticated():
            return self.deny(request)
        self.request = request
        return self.call(*args,**kwargs)
    @classmethod
    def __call__(cls,request,*args,**kwargs):
        return cls.__real_call__(request,*args,**kwargs)
        # Comment above and uncomment below to to enable profilling. Adjust the number below to change % of requests that are profiled.
        #import random
        #if random.random() < 0.1:
        #    return cls.__profile_call__(request,*args,**kwargs)
        #else:
        #    return cls.__real_call__(request,*args,**kwargs)
    def call(self,*args,**kwargs):
        """ Overideable entry point for all request."""
        return self.DISPATCH[self.request.method](*args,**kwargs)
    def change_permission(self,method,auth_required=True):
        """ Change permissions for a given method """
        if auth_required:
            self.auth_required.add(method)
        elif not auth_required and method in self.auth_required:
            self.auth_required.remove(method)
    def error(self,code):
        if code == 404:
            return HttpResponseNotFound("404 Not Found")
        return HttpResponseNotFound("404 Not Found")
    def get(self,*args,**kwargs):
        return HttpResponseNotFound("404 Not Found")
    def delete(self,*args,**kwargs):
        return HttpResponseNotFound("404 Not Found")
    def post(self,*args,**kwargs):
        return HttpResponseNotFound("404 Not Found")
    def put(self,*args,**kwargs):
        return HttpResponseNotFound("404 Not Found")
    def render(self,data):
        if self.template:
            c = Context(data,autoescape=False)
            return HttpResponse(self.template.render(c))
        return HttpResponse(str(data))
    def render_javascript(self,data):
        out = HttpResponse(data)
        out["Content-Type"] = "application/javascript"
        return out
    def render_json(self,data,remove_white_space=False):
        out = simplejson.dumps(data)
        if remove_white_space:
            out = out.replace(' ','')
        if 'callback' in self.request.GET:
            out = '%s(%s)'%(self.request.GET['callback'],out)
            out = HttpResponse(out)
            out["Content-Type"] = "application/javascript"
            return out
        return HttpResponse(out)
    def render_png(self,data):
        out = HttpResponse(data)
        out["Content-Type"] = "image/png"
        out["Cache-Control"] = "max-age=18000, must-revalidate"
        return out
#self.response.headers["Cache-Control"] = TILE_LIFE_SPAN

    def deny(self,request):
        if self.format == 'json':
            if "HTTP_AUTHORIZATION" in request.META:
                aheader = request.META['HTTP_AUTHORIZATION']
            else:
                aheader = "No Authorization Header!"
            d = {'Authorization Header':aheader,'string2sign':self.__unsigned_string,'status':"ACCESS DENIED"}
            return HttpResponseForbidden(simplejson.dumps(d))
        else:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.path)
