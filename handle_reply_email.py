import logging, email
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app

class ReplyHandler(InboundMailHandler):
    def receive(self, msg):
        logging.info("Reply handler received a message from: " + msg.sender)
    

def main():
    application = webapp.WSGIApplication([ReplyHandler.mapping()], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
