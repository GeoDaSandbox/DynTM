from django.conf.urls.defaults import *
import views
import test_views

"""
URLS for the Dictionary Webservice,
To install this Django App in your Django Project, edit your projects urls.py
and include, "(r'^path_to_dict', include('geodaWebService.dict.urls'))," in urlpatterns

"""
html_dtm = views.DTMHandler()
json_dtm = views.DTMHandler('json')
urlpatterns = patterns('',
    (r'^.json/tileset(?:/(?P<tsid>[^/?]*)[/]?)?.*$',views.TileSetHandler('json')),
    (r'^.json/cl(?:/(?P<clid>[^/?]*)[/]?)?.*$',views.ClassificationHandler('json')),
    (r'^.json/colors(?:/(?P<csid>[^/?]*)[/]?)?.*$',views.ColorSchemeHandler('json')),
    (r'^/t.*',views.TileHandler()),
    (r'^/r.*',views.RawTileHandler()),
    #(r'^/tileset(?:/(?P<tsid>[^/?]*)[/]?)?.*$',views.TileSetHandler()),
    (r'^$', html_dtm),
    (r'^/$', html_dtm),
    (r'^_test.png$', test_views.TestHandler()),
    (r'^.json/.*$', json_dtm),
    (r'^.json/$', json_dtm),
)

""" Example Urls to match...
Once the application is installed, for example as /dtm/...
/dtm/
"""
#(prefix+r'/gmap.*',GMapHandler),
#(prefix+r'/query.*', QueryHandler),
#(prefix+r'/classify.*', ClassifyHandler),
#(prefix+r'/colors.*',ColorSchemeHandler),
#(prefix+r'/legend.*',LegendHandler),
#(prefix+r'/o.png.*', OverviewHandler),
#(prefix+r'/o/.*', OverviewHandler),
#(prefix+r'/ids.csv.*', TileSetIdsHandler),
#(prefix+r'/m/.*', TileSetHandler),
#(prefix+r'/t/.*', TileHandler),
#(prefix+r'/.*', DTMHandler),
