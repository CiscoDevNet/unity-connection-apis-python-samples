# Copyright (c) 2020 Cisco and/or its affiliates.
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from flask import Flask, request
import requests
from requests.auth import HTTPBasicAuth
import logging
from http.client import HTTPConnection
import os

# Edit .env file to specify your Webex integration client ID / secret
from dotenv import load_dotenv
load_dotenv()

# Change to true to enable request/response debug output
DEBUG = False

# Instantiate the Flask application
app = Flask(__name__)

# The Flask web app routes start below

# This is the entry point of the app - navigate to https://localhost:5000 to start
@app.route('/incomingMessages', methods = [ 'POST' ] )
def incomingMessage():

    print( request.data )

    return ( '', 200 )

# At startup, setup a recurring CUNI subscription

# resourceType: ignored, leave empty
# eventTypeList: can be ALL_EVENTS or one or more of: 
#       MESSAGE_INFO, NEW_MESSAGE, OPENED_MESSAGE, SAVED_MESSAGE, UNREAD_MESSAGE, 
#       DELETED_MESSAGE, FAILOVER, NO_EVENTS, SUB_END, SUB_EXP, KEEP_ALIVE
# resourceIdList: one or more VM user ids/aliases
# callbackServiceUrl: Complete URL where notifcations should be sent
# expiration: xsd:dateTime/ISO 8601 format time when the subscription expires
# keepAliveInterval: 0 or 1 to disable or enable keepalive messages
subReq = f'''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:even="http://unity.cisco.com/messageeventservice/event" xmlns:even1="http://event.messageeventservice.unity.cisco.com">
<soapenv:Header/>
<soapenv:Body>
    <even:subscribe>
        <even:resourceType/>
        <even:eventTypeList>
            <even:string>ALL_EVENTS</even:string>
        </even:eventTypeList>
        <even:resourceIdList>
            <even:string>{ os.getenv( "VM_USER_1" ) }</even:string>
            <even:string>{ os.getenv( "VM_USER_2" ) }</even:string>
        </even:resourceIdList>
        <even:callbackServiceInfo>
            <even1:callbackServiceUrl>http://{ os.getenv( "APP_HOST_ADDRESS" ) }:{ os.getenv( "APP_PORT" ) }/incomingMessages</even1:callbackServiceUrl>
        </even:callbackServiceInfo>
        <even:expiration>2020-05-02T18:04:00Z</even:expiration>
        <even:keepAliveInterval>1</even:keepAliveInterval>
    </even:subscribe>
</soapenv:Body>
</soapenv:Envelope>'''

print( subReq )

log = logging.getLogger('urllib3')
log.setLevel(logging.DEBUG)

# logging from urllib3 to console
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

# print statements from `http.client.HTTPConnection` to console/stdout
HTTPConnection.debuglevel = 1

resp = requests.post( 
    f'https://{ os.getenv( "CUC_ADDRESS" ) }/messageeventservice/services/MessageEventService',
    auth=HTTPBasicAuth( os.getenv( 'APP_USER' ), os.getenv( 'APP_PASSWORD' ) ),
    headers = { 'Content-Type': 'text/xml', 'SOAPAction': '""' },
    data = subReq,
    verify = False
    )

print( resp, resp.content )    