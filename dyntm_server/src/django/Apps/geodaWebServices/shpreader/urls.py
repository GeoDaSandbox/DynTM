from django.conf.urls.defaults import *
import views

"""
URLS for the Calculator Webservice,
To install this Django App in your Django Project, edit your projects urls.py
and include, "(r'^path_to_calc', include('GeodaWebService.calc.urls'))," in urlpatterns

"""
reader = views.ShpReader('html')
jsonreader = views.ShpReader('json')
urlpatterns = patterns('',
    (r'^/(\w*)/(\d*)x?(\d*)$', reader),
    (r'^.json/(\w*)/(\d*)x?(\d*)$', jsonreader),
    (r'^.*', reader),
)

""" Example Urls to match...
Once the application is installed, for example as /calc/...
/calc/1234+5413
/calc/1234-5413
/calc/1234*5413
/calc/1234/5413
"""
