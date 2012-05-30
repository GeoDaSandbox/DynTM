from django.conf.urls.defaults import *
import views

"""
URLS for the Dictionary Webservice,
To install this Django App in your Django Project, edit your projects urls.py
and include, "(r'^path_to_dict', include('geodaWebService.dict.urls'))," in urlpatterns

"""
html_dict = views.Dict()
json_dict = views.Dict('json')
urlpatterns = patterns('',
    (r'^/(.*)$', html_dict),
    (r'^.json/(.*)$', json_dict),
    (r'^/$', html_dict),
)

""" Example Urls to match...
Once the application is installed, for example as /dict/...
/dict/1234+5413
/dict/1234-5413
/dict/1234*5413
/dict/1234/5413
"""
