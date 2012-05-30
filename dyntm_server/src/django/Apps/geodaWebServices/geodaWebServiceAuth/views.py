from django.http import HttpResponse
from django.template import Template
from geodaWebServices import WebService
from models import GWS_User,GWS_AccessKey

class UserEditor(WebService):
    form = """<html><body>
    Welcome, {{full_name}}...<br>
    <br>
    {{dump}}
    </body></html>"""
    def __init__(self,format='HTML'):
        t = Template(self.form)
        WebService.__init__(self,format,t,auth_required=True)
    def get(self):
        user = self.request.user
        gwsUser = GWS_User.get(user.username)
        keys = GWS_AccessKey.select("user",user.username)
        s = "You have %d access key(s):<br>"%len(keys)
        for k in keys:
            s+=k.key_name+"<br>"
        return self.write({"full_name":user.get_full_name(),"dump":s})
    def index(self):
        # This should be a template for the web service's home page. (if there is one)
        return self.get()
