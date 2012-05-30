#!/usr/bin/env python
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
import logging

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.getAbilities()

    def getAbilities(self):
        #user = users.get_current_user()
        if users.is_current_user_admin():
            self.response.out.write('\n\n\nPostPublic\n\n\n')
            self.response.out.write( "<A HREF='%s'>logout</a>"%users.create_logout_url('/test') )
        else:
            self.response.out.write('None')
            return
def main():
    application = webapp.WSGIApplication([
                                          ('.*', MainHandler)
                                        ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
