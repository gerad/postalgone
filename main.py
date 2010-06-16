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
import urllib

import pdb, sys
debugger = pdb.Pdb(stdin=sys.__stdin__, stdout=sys.__stdout__)

class MailHandler(webapp.RequestHandler):
  def get(self):
    self.send_mail()
    callback = self.request.get('callback')
    if callback:
      self.response.out.write(callback + '({ok: true})')
    else:
      self.redirect_to_finish()

  def post(self):
    self.send_mail()
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
    msg = mail.EmailMessage()
    msg.sender = self.request.get('sender', default_value ="Postal Gone <mail@postalgone.com>")
    from_line = 'Postal Gone message from ' + self.request.get('from', default_value="Anonymous")
    msg.to = self.request.get('to', default_value="Postal Gone <mail@postalgone.com>")
    msg.subject = self.request.get('subject') or from_line
    msg.body = (self.request.get('body', default_value="Empty message") +
      "\n\n" + from_line +
      "\n" + "http://www.postalgone.com/")
    msg.send()

def main():
  application = webapp.WSGIApplication([
    ('/mail', MailHandler)], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
