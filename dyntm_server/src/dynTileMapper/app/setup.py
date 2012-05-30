import sys,os

if __name__=='__main__':
    if len(sys.argv) == 1:
        print "going to build now"
        if sys.platform == 'darwin':
            import py2app
            sys.argv.append('py2app')
        elif sys.platform == 'win32':
            import py2exe
            sys.argv.append('py2exe')

from distutils.core import setup
if sys.platform == 'darwin':
    setup( app=['DynamicTileMapper.py'] )
elif sys.platform == 'win32':
    setup(
        options = {'py2exe': {'bundle_files':3}},
        windows=[{'script': "DynamicTileMapper.py", 
                  'icon_resources': [(1, 'geodaspace.ico')]}],
        zipfile = None
    )

