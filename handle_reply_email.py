import logging, email
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app
from models import *
from encode import *
import re

reply_re = re.compile( '.*r\..+@%s' % mail_domain() )

def reply_subject( subj ):
    if subj.lower().startswith('re: '):
        return subj
    return 'Re: ' + subj

class ReplyHandler(InboundMailHandler):
    def receive(self, msg):
        recipients = msg.to
        #if 'cc' in dir( msg ):
        #    recipients = recipients + msc.cc
        logging.info("Reply handler received a message from %s to %s" % ( msg.sender, str( recipients ) ))
        
        acct = account_for_sender( msg.sender )
        
        # Unauthorized
        if not acct:
            logging.info( "Sender %s unauthorized. Dropping." % msg.sender )
            mail.send_mail( sender=from_field( 'noreply' ), to=msg.sender,
                            subject=reply_subject( msg.subject ),
                            body="I don't know you." )
            return
        
        rcpt, _id = None, None
        #for addr in recipients:
        #    logging.info( addr )
        #    if reply_re.match( addr ):
        #        rcpt = addr
        #        break
        rcpt = msg.to
        
        try:
            logging.info( 'received to %s' % rcpt )
            _id = address_to_id( rcpt )
            logging.info( 'with ID %d' % _id )
            r = Reminder.get_by_id( _id )
        except:
            logging.info( 'Failed to find parseable recipient in %s' % str( recipients ) )
            mail.send_mail( sender=from_field( 'noreply' ), to=msg.sender,
                            subject=reply_subject( msg.subject ),
                            body="I don't know where you were trying to send that." )
            return
        
        bodies = msg.bodies( content_type='text/plain' )
        allBodies = ""
        for body in bodies:
            # body[0] = "text/plain"
            # body[1] = EncodedPayload --> body[1].decode()
            if allBodies:
                allBodies = allBodies + "\n---------------------------\n"
            allBodies = allBodies + body[1].decode()
        
        cmd = allBodies.splitlines()[0] # the first plain-text line
        logging.info('Reply command: ' + cmd)
        
        try:
            r.parse_and_update( cmd.strip(), acct.tz )
            r.put()
        except:
            logging.info( 'Failed to parse update command %s' % cmd )
            mail.send_mail( sender=rcpt, to=msg.sender,
                            subject=reply_subject( msg.subject ),
                            body='I failed to perform the requested schedule update "%s"' % cmd )
            return
    

def main():
    application = webapp.WSGIApplication([ReplyHandler.mapping()], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
