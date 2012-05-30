from django.http import HttpResponse,HttpResponseRedirect
from django.template import Template
from django.core.exceptions import ObjectDoesNotExist
from geodaWebServices import WebService
from models import Dictionary_Entry
#from django.conf import settings

class Dict(WebService):
    form = """<html><body>
        {{key}}: {{value}}
        <br>
        <hr><br>
        <form method='POST' action='/dict/{{key}}'>
        {{key}} = <input name="value" type="text" />
        <input type='submit' />
        </form></body></html>"""
    def __init__(self,format='HTML'):
        t = Template(self.form)
        WebService.__init__(self,format,t,auth_required=True)
    def get(self,key=None):
        if not key:
            return self.index()
        elif key == 'KEYS':
            return self.write(list(Dictionary_Entry.objects.values_list('key',flat=True)))
        elif key == 'VALUES':
            return self.write(list(Dictionary_Entry.objects.values_list('value',flat=True)))
        try:
            result = Dictionary_Entry.objects.filter(user=self.request.user,key=key).get()
            return self.write({'key':key,'value':result.value})
        except ObjectDoesNotExist:
            return self.write({'user':self.request.user.email,'key':key,'value':''})
    def post(self,key):
        value = self.request.POST['value']
        try:
            e = Dictionary_Entry.objects.filter(user=self.request.user,key=key).get()
            e.value = value
        except ObjectDoesNotExist:
            e = Dictionary_Entry(user=self.request.user, key=key, value=value)
        e.save()
        return self.write({'key':key,'value':value})
    def index(self):
        # This should be a template for the web service's home page. (if there is one)
        return HttpResponse('Welcome to my Dictionary Web Service!')


