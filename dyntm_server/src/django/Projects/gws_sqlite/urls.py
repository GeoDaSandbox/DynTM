from django.conf.urls.defaults import *
import django.contrib.auth.views
from django.conf import settings
from django.views.generic.simple import redirect_to

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^myproj/', include('myproj.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^user', include('geodaWebServices.geodaWebServiceAuth.urls')),
    (r'^calc', include('geodaWebServices.calc.urls')),
    (r'^dict', include('geodaWebServices.dict.urls')),
    (r'^dyntm', include('geodaWebServices.dyntm.urls')),
    (r'^classifier', include('geodaWebServices.classification.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^favicon.ico$', redirect_to, {'url':settings.MEDIA_URL+'/favicon.ico'}),
)

