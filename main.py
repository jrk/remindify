#!/usr/bin/env python

import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from google.appengine.api import mail
from datetime import datetime
import logging
from models import *
from encode import *
#import key

def notify(user, text, title, link=None):
    params = {'text':text,'title':title, 'icon': 'http://www.remindify.com/favicon.ico'}
    if link:
        params['link'] = link
    #urlfetch.fetch('http://api.notify.io/v1/notify/%s?api_key=%s' % (hashlib.md5(user.email()).hexdigest(), key.api_key), method='POST', payload=urllib.urlencode(params))
    # TODO: update to send mail, with untique address per-reminder


class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        failed = self.request.get('failed')
        if user:
            account = Account.all().filter('user =', user).fetch(10)
            logout_url = users.create_logout_url("/")
            #reminders = Reminder.all().filter('user =', user).filter('fired =', False).fetch(1000)
            reminders = Reminder.all().filter('user =', user).fetch(1000)
            reminders = [r for r in reminders if not r.fired]
            if account:
                assert len(account) == 1
                account = account[0]
            else:
                # Create account if it doesn't yet exist
                account = Account(user=user)
                account.put()
            emails = ', '.join( account.emails )
        else:
            login_url = users.create_login_url('/')
        timezones = Account.timezones
        self.response.out.write(template.render('main.html', locals()))
    
    def post(self):
        user = users.get_current_user()
        account = Account.all().filter('user =', user).fetch(1)[0]
        if self.request.get('id'):
            reminder = Reminder.get_by_id(int(self.request.get('id')))
            if reminder.user == user:
                reminder.delete()
        elif self.request.get('tz'):
            account.tz = self.request.get('tz')
            account.emails = [ e.strip() for e in self.request.get('emails').split(',') ]
            account.put()
        else:
            if not create_reminder( self.request.get('raw'), account.tz, account.user ):
                return self.redirect('/?failed=1')
            #notify(user, str(reminder.scheduled_local()), "Reminder Scheduled")
        self.redirect('/')
    

def send_reminder( reminder ):
    address = id_to_address( reminder.key().id() )
    mail.send_mail( sender=address, to=reminder.user.email(),
                    subject=reminder.text,
                    body="On %s you asked to be reminded:\n\n\t%s\n\nat %s" % ( str(reminder.created), reminder.raw, str(reminder.scheduled))
                )

class CheckHandler(webapp.RequestHandler):
    def get(self):
        while True:
            #reminders = Reminder.all().filter('fired =', False).filter('scheduled <=', datetime.now()).fetch(1000)
            reminders = Reminder.all().filter('scheduled <=', datetime.now()).fetch(1000)
            reminders = [r for r in reminders if not r.fired]
            if not reminders:
                break
            for reminder in reminders:
                send_reminder(reminder)
                reminder.fired = True
                reminder.put()
        self.response.out.write("ok")

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler), 
        ('/check', CheckHandler),
        ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()

