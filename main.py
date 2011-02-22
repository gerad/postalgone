#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import mail
from google.appengine.ext import db
import pprint
import urllib
import logging
import traceback

import pdb, sys
debugger = pdb.Pdb(stdin=sys.__stdin__, stdout=sys.__stdout__)

class Email(db.Model):
  sender = db.StringProperty(default="Postal Gone <mail@postalgone.com>")
  to = db.StringProperty(default="Anonymous")
  subject = db.StringProperty(default="Message from Postal Gone")
  body = db.TextProperty()
  html = db.TextProperty()
  debug = db.BooleanProperty(default=False)
  request = db.TextProperty()
  sent_at = db.DateTimeProperty(auto_now=True)

  @classmethod
  def from_request(cls, request):
    email = cls()
    for k, p in cls.properties().iteritems():
      if k not in ['request', 'sent_at', 'debug']:
        v = request.get(k, default_value=p.default_value())
        setattr(email, k, v)
    email.debug = bool(request.get('debug', default_value=False))
    email.request = "\n".join([
      "\nparams:", pprint.pformat(dict(request.params)),
      "\nenviron:", pprint.pformat(request.environ),
      "\nheaders:", pprint.pformat(request.headers)])
    return email

  def send(self):
    msg = mail.EmailMessage(sender=self.sender, to=self.to, subject=self.subject)
    if self.html: msg.html = self.html
    msg.body = (self.body or ' ')
    if self.debug: msg.body += "\n%s" % self.request

    msg.send()
    self.put()

class MailHandler(webapp.RequestHandler):
  def get(self):
    if self.send_mail():
      callback = self.request.get('callback')
      if callback:
        self.response.out.write(callback + '({ok: true})')
      else:
        self.redirect_to_finish()

  def post(self):
    if self.send_mail():
      self.redirect_to_finish()

  def redirect_to_finish(self, other=None):
    location = self.request.get('location')
    env = self.request.environ
    if location:
      self.redirect(location)
    elif 'HTTP_REFERRER' in env:
      self.redirect('/thanks?' + urllib.urlencode({"return_to": env['HTTP_REFERRER']}))
    elif 'HTTP_REFERER' in env:
      self.redirect('/thanks?' + urllib.urlencode({"return_to": env['HTTP_REFERER']}))
    else:
      self.redirect('/thanks')

  def send_mail(self):
    try:
      Email.from_request(self.request).send()
    except Exception, err:
      self.error(500)
      logging.error(traceback.format_exc())
      self.response.out.write(str(err))
      return False
    return True

def main():
  application = webapp.WSGIApplication([
    ('/mail', MailHandler)], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
