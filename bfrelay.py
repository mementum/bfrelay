#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
# 
# Copyright (C) 2014 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import sys

import httxlib

showMessages = True

class FlushFile(object):
    '''
    Class to flush stdout and stderr instantly
    '''
    def __init__(self, f):
        self.f = f

    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = FlushFile(sys.stdout)
sys.stderr = FlushFile(sys.stderr)

httxmanager = httxlib.HttxManager()
httxmanager.options.skiprealdecomp = False

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(404, 'Not found')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write('Not found')
        return

    def do_POST(self):
        # Check the magic header
        if 'bfpphome' not in self.headers:
            self.send_response(404, 'Not found')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('Not found')
            return

        # 1. Parse URL (URL:....)
        url = ':'.join(self.rfile.readline().split(':')[1:]).rstrip('\n')
        # 2. Parse headers (HEADERS: {...})
        headers = eval(':'.join(self.rfile.readline().split(':')[1:]))
        # 3. Skip the 'MESSAGE:' line
        self.rfile.readline()
        # 4. Read and add until we see the closing </SOAP ...
        message = str()
        while True:
            line = self.rfile.readline()
            message += line
            if line.lower().startswith('</soap:envelope'):
                break
                
        # message = message.rstrip()
        # message += '\r\n'
        # headers['content-length'] = str(len(message))

        # Use the parsed elements to generate a new HTTP request
        httxrequest = httxlib.HttxRequest(url=url, headers=headers, data=message)
        if showMessages:
            print "------------------>>>"
            print "Sending:"
            print "URL: %s" % url
            print "HEADERS: %s" % str(headers)
            print "MESSAGE: %s" % message
            print "---------------------"
        try:
            httxresponse = httxmanager.urlopen(httxrequest)

            if showMessages:
                print "Received:"
                print "STATUS: %s" % str(httxresponse.status)
                print "HEADERS: %s" % str(httxresponse.headers)
                if not httxmanager.options.skiprealdecomp:
                    print "MESSAGE: %s" % httxresponse.body
                print "<<<<---------------------"

            self.send_response(int(httxresponse.status))
            for name, value in httxresponse.headers:
                # We have decompressed the body, se we skip that
                # We could always recompress it
                if name.lower() == 'transfer-encoding':
                    continue
                if not httxmanager.options.skiprealdecomp and name.lower() == 'content-encoding':
                    continue
                # Use the "content-length" hint to replace the original value
                if not httxmanager.options.skiprealdecomp and name.lower() == 'content-length':
                    # self.send_header(name.lower(), str(len(httxresponse.body) + len('\r\n')))
                    self.send_header(name, httxresponse.getheader('cteonnt-length'))
                    continue
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(httxresponse.body + '\r\n')
        except Exception, e:
            print "exception e %s" % str(e)
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('Error in connection')

        return


def main():
    try:
        server = HTTPServer(('', 2379), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()

