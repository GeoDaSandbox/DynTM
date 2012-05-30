import boto
import config
try:
    aws_accesskeyid = config.aws_accesskeyid
    aws_accesskey = config.aws_accesskey
except:
    if config.DEBUG: print "AWS Access Keys Not Set, Please edit config.py"
    aws_accesskeyid = None
    aws_accesskey = None

def s3_upload(bucket_name, key_name, contents, public=False, overwrite=False):
    if aws_accesskeyid and aws_accesskey:
        try:
            s3 = boto.connect_s3(aws_accesskeyid,aws_accesskey)
            b = s3.get_bucket(bucket_name)
            if b.get_key(key_name) and not overwrite:
                if config.DEBUG: print "Key_name: %s allready exists"%key_name
                return False
            key = b.new_key(key_name)
            key.set_contents_from_string(contents)
            if public:
                key.set_acl('public-read')
            else:
                key.set_acl('private')
            return "http://%s.%s/%s"%(bucket_name,s3.host,key.name)
        except:
            if config.DEBUG: raise
            return False
    else:
        return False
