from config import BACKEND
#BACKEND = 'google'
#BACKEND = 'standalone'
if BACKEND == 'google':
    from google.appengine.ext import db
    from google.appengine.api import memcache
elif BACKEND == 'standalone':
    from config import db_location
    import db
    db.DB = db_location
    from fake_memcache import memcache
elif BACKEND == 'amazonSimpleDB':
    from config import aws_accesskey,aws_accesskeyid
    import sdb as db
    db.aws_accesskeyid = aws_accesskeyid
    db.aws_accesskey = aws_accesskey
    try:
        from memcache import Client
        memcache = Client(['127.0.0.1:11211'], debug=0)
    except:
        from fake_memcache import memcache
