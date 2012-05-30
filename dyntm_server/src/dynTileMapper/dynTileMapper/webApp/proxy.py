#!/usr/bin/env python
"""
Gets around the cross server restrictions of AJAX
"""
import os
import logging
import urllib
import sys
from google.appengine.api import urlfetch

url = sys.stdin.read()
try:
    url,body = url.split('?')
    url = urlfetch.fetch(url,body,method='POST')
    #logging.info(url.headers)
    #logging.info(url.content)
except urlfetch.InvalidURLError:
    logging.info('URL IS INVALID:')
    logging.info(url)
    raise
for header,value in url.headers.iteritems():
    print header+':',value
print
print url.content
