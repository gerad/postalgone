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
import urllib
import logging
import traceback

import pdb, sys
debugger = pdb.Pdb(stdin=sys.__stdin__, stdout=sys.__stdout__)

class Email(db.Model):
  sent_at = db.DateTimeProperty(auto_now=True)
  sender = db.StringProperty(default="Postal Gone <mail@postalgone.com>")
  to = db.StringProperty(default="Anonymous")
  subject = db.StringProperty(default="Message from Postal Gone")
  body = db.TextProperty()
  html = db.TextProperty()

  @classmethod
  def send(cls, request):
    log = cls()
    msg = mail.EmailMessage()
    for k, p in cls.properties().iteritems():
      if k == 'sent_at': continue

      v = request.get(k, default_value=None)
      if v: setattr(log, k, v)
      else: v = p.default_value()
      if v: setattr(msg, k, v)
    msg.send()
    log.put()

class MailHandler(webapp.RequestHandler):
  def get(self):
    if not self.send_mail(): return
    callback = self.request.get('callback')
    if callback:
      self.response.out.write(callback + '({ok: true})')
    else:
      self.redirect_to_finish()

  def post(self):
    if not self.send_mail(): return
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
      Email.send(self.request)
      return True
    except Exception, err:
      self.error(500)
      logging.error(traceback.format_exc())
      self.response.out.write(str(err))
      return False

def main():
  application = webapp.WSGIApplication([
    ('/mail', MailHandler)], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
