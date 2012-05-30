import sys
import os.path

DEBUG = True
#Google AppEngine Config
#BACKEND = 'google'
#db_location = None

#Standalone Config
BACKEND = 'standalone'
db_location = '/var/tmp/dtm/'
if not os.path.exists(db_location):
    os.mkdir('/var/tmp/dtm/')
MAP_FILE_HOME = '/var/maps/'

#Amazon SimpleDB Config
#BACKEND = 'amazonSimpleDB'
#try:
#    if sys.platform == 'darwin':
#        aws_accesskeyid = open(os.path.expanduser('~/.ec2/accesskeyid'),'r').read().strip()
#        aws_accesskey = open(os.path.expanduser('~/.ec2/accesskey'),'r').read().strip()
#    elif sys.platform == 'linux2':
#        aws_accesskeyid = open('/home/ubuntu/.ec2/accesskeyid','r').read().strip()
#        aws_accesskey   = open('/home/ubuntu/.ec2/accesskey','r').read().strip()
#except:
#    aws_accesskeyid = ''
#    aws_accesskey   = ''
