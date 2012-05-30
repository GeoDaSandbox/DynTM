from django.conf.urls.defaults import *
import views

"""
URLS for the Calculator Webservice,
To install this Django App in your Django Project, edit your projects urls.py
and include, "(r'^path_to_calc', include('GeodaWebService.calc.urls'))," in urlpatterns

"""
calc = views.Calc()
json_calc = views.Calc('json')
urlpatterns = patterns('',
    (r'^/(\d*\.?\d*)([+\-*/])(\d*\.?\d*)$', calc),
    (r'^.json/(\d*\.?\d*)([+\-*/])(\d*\.?\d*)$', json_calc),
    (r'^/$', calc),
)

""" Example Urls to match...
Once the application is installed, for example as /calc/...
/calc/1234+5413
/calc/1234-5413
/calc/1234*5413
/calc/1234/5413
"""
