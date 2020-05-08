'''
Cisco Unity Connection send message script using the CUMI API

Creates a test user, sets the user's password, then sends a new voicemail 
message with audio file attachment.  Finally, deletes all messages in the
user's inbox and deletes the user.

Copyright (c) 2020 Cisco and/or its affiliates.
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import requests
from requests import Request, Session
from requests.auth import HTTPBasicAuth
import logging
from http.client import HTTPConnection
import os
import sys
import json

# Edit .env file to specify your Webex integration client ID / secret
from dotenv import load_dotenv
load_dotenv()

# Change to true to enable request/response debug output
DEBUG = False

if DEBUG:
    print()
    log = logging.getLogger('urllib3')
    log.setLevel(logging.DEBUG)

    # logging from urllib3 to console
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    log.addHandler(ch)

    # print statements from `http.client.HTTPConnection` to console/stdout
    HTTPConnection.debuglevel = 1

# Create a basic new user object for testUser1
req = {
    'Alias': 'testUser1',
    'DtmfAccessId': '987654321'
}

try:
    resp = requests.post( 
        f'https://{ os.getenv( "CUC_ADDRESS" ) }/vmrest/users?templateAlias=voicemailusertemplate',
        auth = HTTPBasicAuth( os.getenv( 'APP_USER' ), os.getenv( 'APP_PASSWORD' ) ),
        json = req,
        verify = False
        )

    # Raise an exception if a non-200 HTTP response received
    resp.raise_for_status()
    
except Exception as err:

    print( f'Request error: POST ../users: { err }' )
    sys.exit( 1 )

userId = resp.headers['Location'].split( '/' )[ -1 ]

print( f'\n POST ../users: Created user Id: { userId }\n' )

input( 'Press Enter to continue...' )

#Set the password for the new user

#CredentailType 3 = password, 4 = pin
req = {
    'Credentials': '0xFt3i4#%p$V',
    'CantChange': False,
    'DoesntExpire': True,
    'Locked': False,
    'CredMustChange': False
}    

try:
    resp = requests.put( 
        f'https://{ os.getenv( "CUC_ADDRESS" ) }/vmrest/users/{ userId }/credential/password',
        auth = HTTPBasicAuth( os.getenv( 'APP_USER' ), os.getenv( 'APP_PASSWORD' ) ),
        json = req,
        verify = False
        )

    # Raise an exception if a non-200 HTTP response received
    resp.raise_for_status()
    
except Exception as err:

    print( f'Request error: PUT ../users/{ userId }/credential/password: { err }\n' )
    sys.exit( 1 )

print( f'\n PUT ../users/{ userId }/credential/password: Success\n' )

input( 'Press Enter to continue...' )

# Create a new message with audio attachment
message = json.dumps( {
    'Subject': 'testMessage',
    'Priority': 'Normal',
    'Sensitivity': 'Normal',
    'ReadReceiptRequested': False,
    'Secure': True
} )

# Send to ourself
recipients = json.dumps( {
    'Recipient': [
        {
            'Type': 'TO',
            'Address': { 'SmtpAddress': f'testuser1@{ os.getenv( "CUC_ADDRESS" ) }' }
        }
    ]
} )

# Read the audio file (WAV/mono/44Khz)
# Formats: see 'User Guide for the Cisco Unity Connection Messaging Assistant Web Tool'
with open('message.wav', 'rb') as f:

    audioFile = f.read( )

#CUMI does not appear to like Content-Disposition multi-part headers
#   creeted by Requests when using the 'files' option.  We'll need to build the body
#   from scratch and use a prepared request
requestBody = (
    b'--the_message_boundary\r\n' +
    b'Content-Type: application/json\r\n\r\n' +
    bytes( message, 'utf-8' ) + b'\r\n' +
    b'--the_message_boundary\r\n' +
    b'Content-Type: application/json\r\n\r\n' +
    bytes( recipients, 'utf-8' ) + b'\r\n' +
    b'--the_message_boundary\r\n' +
    b'Content-Type: audio/wav\r\n\r\n' +
    audioFile + b'\r\n' +
    b'--the_message_boundary--\r\n'
)

# Create a scratch request
req = Request('POST', 
    f'https://{ os.getenv( "CUC_ADDRESS" ) }/vmrest/messages',
    auth = HTTPBasicAuth( 'testUser1', '0xFt3i4#%p$V' ),
    headers = { 'Content-Type': 'multipart/form-data; boundary=the_message_boundary'},
    data = requestBody
)

try:
    # Prepare and send the request
    resp = Session().send( req.prepare(), stream=True, verify = False )  

except Exception as err:
    print( f'Request error: POST ../messages: { err }\n' )
    sys.exit( 1 )

print( '\n POST ../messages: Success\n' )

input( 'Press Enter to continue...' )

# Retrieve the list of messages in the inbox
try:
    resp = requests.get( 
        f'https://{ os.getenv( "CUC_ADDRESS" ) }/vmrest/mailbox/folders/inbox/messages?userobjectid={ userId }',
        auth = HTTPBasicAuth( 'testUser1', '0xFt3i4#%p$V' ),
        headers = { 'Accept': 'application/json' },
        verify = False
    )

    # Raise an exception if a non-200 HTTP response received
    resp.raise_for_status()
    
except Exception as err:

    print( f'Request error: GET ../mailbox/folders/inbox/messages?userobjectid={ userId }: { err }\n' )
    sys.exit( 1 )
    
print( f'\n GET ../mailbox/folders/inbox/messages?userobjectid={ userId }: Messages found: { resp.json()[ "@total" ] }\n' )

messages = resp.json()['Message'] 

# If there are < 2 messages, Message will not be a list.
# We'll stuff it into a list in that case to make our for loop below simpler
messages = messages if isinstance( messages, list ) else [ messages ]

input( 'Press Enter to continue...' )

# Delete all the messages in the inbox
for message in messages:

    try:
        resp = requests.delete( 
            f'https://{ os.getenv( "CUC_ADDRESS" ) }/vmrest/messages/{ message[ "MsgId" ] }',
            auth = HTTPBasicAuth( 'testUser1', '0xFt3i4#%p$V' ),
            verify = False
        )

        # Raise an exception if a non-200 HTTP response received
        resp.raise_for_status()

    except Exception as err:

        print( f'Request error: DELETE ../messages/{ message[ "MsgId" ] } { err }\n' )
        sys.exit( 1 )    

print( f'\n DELETE ../messages: Success\n' )

input( 'Press Enter to continue...' )

# Delete the user we just created
try:
    resp = requests.delete( 
        f'https://{ os.getenv( "CUC_ADDRESS" ) }/vmrest/users/{ userId }',
        auth = HTTPBasicAuth( os.getenv( 'APP_USER' ), os.getenv( 'APP_PASSWORD' ) ),
        verify = False
        )

    # Raise an exception if a non-200 HTTP response received
    resp.raise_for_status()

except Exception as err:

    print( f'Request error: DELETE ../users: { err }' )
    sys.exit( 1 )

print( f'\n DELETE ../users/{ userId }: Success\n' )