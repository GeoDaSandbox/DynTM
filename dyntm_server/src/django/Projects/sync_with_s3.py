import mimetypes
import os,boto

keyidpath = '~/.ec2/accesskeyid'
keypath = '~/.ec2/accesskey'
bucket_name = 'media2.geodacenter.org'
PATH_TO_SYNC = 'static/'
#local_folders = ['.','js','css','images']

KEYID = open(os.path.expanduser(keyidpath),'r').read().strip()
KEY = open(os.path.expanduser(keypath),'r').read().strip()
s3 = boto.connect_s3(KEYID,KEY)

b = s3.get_bucket(bucket_name)
key_names=set()


def upload(key,name,local_file,local_file_name=''):
    print "Uploading local version..."
    #mime = mimetypes.guess_type(local_file_name)[0]
    #if mime:
    #    print local_file_name,'is',mime
    #    headers = {'Content-Type':mime}
    #    key.set_contents_from_string(local_file)
    if local_file_name:
        key.set_contents_from_filename(local_file_name)
    else:
        key.set_contents_from_string(local_file)
    if 'private' in name:
        print "Setting ACL...PRIVATE"
        key.set_acl('private')
    else:
        print "Setting ACL...READONLY"
        key.set_acl('public-read')


for key in b.get_all_keys():
    name = os.path.join(PATH_TO_SYNC,key.name)
    key_names.add(key.name)
    if os.path.exists(name):
        remote_file = key.get_contents_as_string()
        local_file = open(name,'r').read()
        if remote_file == local_file:
            print "\t\tNo Diffs:", name
        else:
            print name," has local modifications"
            upload(key,key.name,local_file)
            print "Done."
    else:
        if not name.endswith('$folder$'):
            print "NO LOCAL version of:",name
for path,dirnames,filenames in os.walk(PATH_TO_SYNC):
    if '/.' in path:
        pass
    else:
        for fname in filenames:
            name = os.path.join(path,fname)
            key_name = name[len(PATH_TO_SYNC):]
            if key_name not in key_names:
                print "No remote version for the local file: ",key_name
                result = raw_input("\tWould you like to add %s to the S2 Bucket? (y/N) "%key_name)
                if result.lower() == 'y':
                    print "ADDING"
                    local_file = open(name,'r').read()
                    key = b.new_key(key_name)
                    upload(key,key_name,local_file,local_file_name=name)
