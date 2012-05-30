# Setup Django for testing outside a server environment.
if __name__=='__main__':
    import sys,os
    sys.path.append('/Users/charlie/Documents/repos/geodacenter/geodaWeb/trunk/django/Projects')
    os.environ['DJANGO_SETTINGS_MODULE']='gws_sqlite.settings'

if __name__=='__main__':
    import time
    #import doctest
    #doctest.testmod()
