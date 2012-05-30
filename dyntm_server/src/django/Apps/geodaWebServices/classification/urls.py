from django.conf.urls.defaults import *
import views

"""
URLS for the Dictionary Webservice,
To install this Django App in your Django Project, edit your projects urls.py
and include, "(r'^path_to_dict', include('geodaWebService.dict.urls'))," in urlpatterns

"""
jsClientAPI = views.JavaScriptClient()
jsServiceAPI = views.JavaScriptService()
json_ch = views.ClassificationHandler('JSON')
urlpatterns = patterns('',
    (r'^\.js$', jsClientAPI),
    (r'^/service\.html$', jsServiceAPI),
    (r'^.*$', json_ch),
)
