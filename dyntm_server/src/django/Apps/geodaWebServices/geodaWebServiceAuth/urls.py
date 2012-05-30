from django.conf.urls.defaults import *
import views

"""
URLS for the Dictionary Webservice,
To install this Django App in your Django Project, edit your projects urls.py
and include, "(r'^path_to_dict', include('geodaWebService.dict.urls'))," in urlpatterns

"""
html_userEditor = views.UserEditor()
urlpatterns = patterns('',
    (r'^/$', html_userEditor),
)

""" Example Urls to match...
Once the application is installed, for example as /user/...
/user/*
"""
