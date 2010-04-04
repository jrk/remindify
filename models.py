from google.appengine.ext import db
from google.appengine.api import urlfetch
import urllib
from dateutil import parser
import logging

def parse_time(tz, text):
    # TODO: modify to parse send-date as well for relative time expressions
    response = urlfetch.fetch('http://www.timeapi.org/%s/%s' % (tz.lower(), urllib.quote(text)))
    if response.status_code == 200:
        return response.content

def create_reminder( s, tz ):
    try:
        reminder = Reminder( parse=s, timezone=tz )
        reminder.put()
        return reminder
    except:
        logging.error( 'Failed to create Reminder for request "%s"' % s )

class Reminder(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    raw = db.StringProperty(required=True)
    text = db.StringProperty()
    scheduled_raw = db.StringProperty()
    scheduled = db.DateTimeProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    
    def __init__(self, *args, **kwargs):
        if 'parse' in kwargs:
            kwargs['text'], kwargs['scheduled_raw'] = self.parse(kwargs['parse'], kwargs['timezone'])
            kwargs['scheduled'] = parser.parse(kwargs['scheduled_raw'])
            kwargs['raw'] = kwargs['parse']
        super(Reminder, self).__init__(*args, **kwargs)
    
    def scheduled_local(self):
        return parser.parse(self.scheduled_raw)
    
    def parse(self, raw, timezone):
        ats = raw.split(' at ')
        if len(ats) == 2:
            return (ats[0], parse_time(timezone, 'at %s' % ats[1]))
        ins = raw.split(' in ')
        if len(ins) == 2:
            return (ins[0], parse_time(timezone, 'in %s' % ins[1]))
        return raw, None
    

class Account(db.Model):
    user = db.UserProperty(required=True)
    emails = db.StringListProperty( )
    tz = db.StringProperty(default='PDT')
    
    timezones = [ 'PST', 'PDT', 'MST', 'MDT', 'CST', 'CDT', 'EST', 'EDT' ]
    
    def __init__(self, *args, **kwargs):
        if 'emails' not in kwargs:
            kwargs['emails'] = []
        if kwargs['user'].email() not in kwargs['emails']:
            kwargs['emails'].append( kwargs['user'].email() )
        
        super(Account, self).__init__(*args, **kwargs)
    
