import logging, email
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import mail
from google.appengine.api.urlfetch import fetch
from models import *

def account_for_sender( sender ):
    accts = Account.gql( "WHERE emails = :sender", sender=sender ).fetch(2)
    if not accts:
        return None
    if len( accts ) > 1:
        logging.error( 'Matched multiple accounts for sender %s---this should not happen' % sender )
        return None
    return accts[ 0 ]


class NewPingHandler(InboundMailHandler):
    def receive(self, msg):
        logging.info( "New handler received a message from %s at %s" % ( msg.sender, msg.date ) )
        
        acct = account_for_sender( msg.sender )
        
        # Unauthorized
        if not acct:
            logging.info( "Sender %s unauthorized. Dropping." % msg.sender )
            mail.send_mail( sender='p@aeping.appspotmail.com', to=msg.sender,
                            subject='Re: '+msg.subject,
                            body="I don't know you." )
            return
        
        candidates = [ msg.subject ]
        #try:
        #    candidates.extend( msg.bodies( content_type='text/plain' )[0].splitlines() )
        #except:
        #    logging.error( 'Found no body of type text/plain' )
        
        # Extract all the non-nil matches
        #matches = [ date_string_re.match( c ) for c in candidates ]
        #cmds = [ m.groups() for m in filter( lambda m: m, matches) ]
        cmds = candidates
        
        if not cmds:
            logging.info( "Message included no recognized command strings" )
            return
        
        failedCmds = []
        
        for cmd in cmds:
            reminder = create_reminder( cmd, acct.tz )
            if not reminder:
                failedCmds.append( cmd )
        
        if failedCmds:
            errMsg = 'I failed to parse the following commands:\n\n%s' % '\n\n'.join( failedCmds )
            logging.error( 'Replying: ' + errMsg )
            mail.send_mail( sender='p@aeping.appspotmail.com', to=msg.sender,
                            subject='Re: '+msg.subject,
                            body=errMsg)
    

def main():
    application = webapp.WSGIApplication([NewPingHandler.mapping()], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
