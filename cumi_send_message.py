'''
Cisco Unity Connection send message script using the CUPI/CUMI APIs

Executes the following sequence:

* Creates a test user
* Sets the user's password
* Performs a user address lookup
* Sends a message with audio file attachment
* Deletes all messages in the user's inbox
* Deletes the user

Copyright (c) 2022 Cisco and/or its affiliates.
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

from time import sleep
import requests
from requests import Request, Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from requests_toolbelt.utils import dump
import urllib3
import os
import sys
import json

print()

# Edit .env file to specify your CUC hostname and API admin user credentials
from dotenv import load_dotenv
load_dotenv( override = True )

# Enable detailed HTTP/XML logging in .env
DEBUG = os.getenv( 'DEBUG' ) == 'True'

# Use request_toolkit to print raw HTTP messages
def logHttp( response ):
    if not DEBUG == True: return
    print( '--------------- Request/Response ---------------' )
    print(
        dump.dump_all(
            response = response,
            request_prefix = None,
            response_prefix = None
        ).decode( 'utf-8', errors='ignore' ), '\n' )

# If the CUC 'tomcat' certificate location is configured in .env,
# enable server certificate checking for requests
if os.getenv( 'CUC_CERT' ):
    certVerify = os.getenv( 'CUC_CERT' )
# Else disable certificate checking
else:
    certVerify = False

# Create a Basic Auth encoded credential
adminCredentials = HTTPBasicAuth( os.getenv( 'APP_USER' ), os.getenv( 'APP_PASSWORD' ) )
adminSession = Session()
adminSession.verify = certVerify
adminSession.auth = adminCredentials

# CUC self-signed certs do no have a (deprecated) subjectAltName,
# disable the warning.
urllib3.disable_warnings( urllib3.exceptions.SubjectAltNameWarning )

# Create a new test user with extension 987654321
req = {
    "Alias": "testUser",
    "DtmfAccessId": "987654321" }

# Note: templateAlias must be provided via URL query parameters
try:
    resp = adminSession.post( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/users',
        params = { 'templateAlias': 'voicemailusertemplate' },
        headers = { 'Content-Type': 'application/json' },
        json = req )
    logHttp( resp )
    resp.raise_for_status()
except HTTPError as err:
    statusCode = err.response.status_code
    print( f'Request error: POST /user Status Code: { statusCode } URL:{ err.response.url }' )
    print( f'Error: { err.response.content.decode( "utf-8" ) }' )
    if statusCode == 400: # Bad Request
        print( 'This error may be due to existing duplicate alias/extension.\n' )
    sys.exit( 1 )

# Parse the new user's ObjectId from the end of the Location header URL
userObjectId = resp.headers[ 'Location' ].split( '/' )[ -1 ]

print( f'POST /users: ObjectId: { userObjectId }\n' )
input( 'Press Enter to continue...\n' )

#Set the password for the new user - this must be done after user creation
# CredentailType 3 = password, 4 = pin
req = {
    'Credentials': '0xFt3i4#%p$V',
    'CantChange': False,
    'DoesntExpire': True,
    'Locked': False,
    'CredMustChange': False }    

try:
    resp = adminSession.put( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/users/{ userObjectId }/credential/password',
        auth = adminCredentials,
        headers = { 'Content-Type': 'application/json' },
        json = req )
    logHttp( resp )
    # Raise an exception if a non-200 HTTP response received
    resp.raise_for_status()
except HTTPError as err:
    statusCode = err.response.status_code
    status = json.loads( err.response.content )[ 'errors' ][ 'code' ]
    print( f'Request error: PUT /password: Status Code:{ statusCode } { status } URL:{ err.response.url }' )
    print( f'Error: { err.response.content.decode( "utf-8" ) }' )
    sys.exit( 1 )

print( f'PUT /password: Success\n' )
input( 'Press Enter to continue...\n' )

# The next four end-user /mailbox operations (search/send/retrieve/dete)
# will need to use the user's credentials/session object

# Create a Basic Auth encoded credential
userCredentials = HTTPBasicAuth( 'testUser', '0xFt3i4#%p$V' )

# Create a separate Session for end-user operations
userSession = Session()
userSession.verify = certVerify
userSession.auth = userCredentials

# Query the mailbox address list using the new user's own name.
try:
    resp = userSession.get( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/mailbox/addresses',
        params = { 'name': 'testUser' },
        headers = { 'Accept': 'application/json' }        )
    logHttp( resp )
    resp.raise_for_status()
except HTTPError as err:
    statusCode = err.response.status_code
    status = json.loads( err.response.content )[ 'errors' ][ 'code' ]
    print( f'Request error: GET /addresses: Status Code:{ statusCode } { status } URL:{ err.response.url }' )
    print( f'Error: { err.response.content.decode( "utf-8" ) }' )
    sys.exit( 1 )

addresses = resp.json()[ 'Address' ]

# If there are < 2 mailbox adresses, Address will be a singleton, not a list,
# so stuff it into a list to making parsing easier
if not isinstance( addresses, list ): mailboxStores = [ addresses ]

# Note: more than one Address could be returned if other
# users' names include 'testUser'
addressObjectId = resp.json()[ 'Address' ][ 0 ][ 'ObjectId' ]

print ( f'GET /addresses: ObjectId: { addressObjectId }\n')
input( 'Press Enter to continue...\n' )

# Create a new message object, convert to string
message = json.dumps( {
    'Subject': 'testMessage',
    'Priority': 'Normal',
    'Sensitivity': 'Normal',
    'ReadReceiptRequested': False,
    'Secure': True } )

# Sending to ourself as the only recipient...
recipients = json.dumps( {
    'Recipient': [
        {
            'Type': 'TO',
            'Address': { 'UserGuid': addressObjectId }
        }
    ] } )

# Read the sample audio file contents from message.wav (WAV/mono/44Khz)
# Formats: see 'User Guide for the Cisco Unity Connection Messaging Assistant Web Tool'
with open('message.wav', 'rb') as f:
    audioFile = f.read( )

#CUMI does not appear to like Content-Disposition multi-part headers
#   created by Requests when using the 'files' option.  We'll need to build the body
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
    b'--the_message_boundary--\r\n' )

# Create a 'scratch' prepared request object
req = Request('POST', 
    f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/messages',
    params = { 'userobjectid': userObjectId },
    auth = userCredentials,
    headers = { 'Content-Type': 'multipart/form-data; boundary=the_message_boundary'},
    data = requestBody )

try:
    # Prepare and send the request
    resp = Session().send( req.prepare(), stream=True, verify = certVerify )
    logHttp( resp )
    resp.raise_for_status()
except HTTPError as err:
    statusCode = err.response.status_code
    status = json.loads( err.response.content )[ 'errors' ][ 'code' ]
    print( f'Request error: POST /messages: Status Code:{ statusCode } { status } URL:{ err.response.url }' )
    print( f'Error: { err.response.content.decode( "utf-8" ) }' )
    sys.exit( 1 )

print( 'POST /messages: Success\n' )
print( 'Waiting a few seconds for the message to be processed...' )
sleep( 10 )
input( 'Press Enter to continue...\n' )

# Retrieve the messages in the inbox to make sure sending it worked
try:
    resp = userSession.get( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/mailbox/folders/inbox/messages',
        params = { 'userobjectid': userObjectId },
        headers = { 'Accept': 'application/json' } )
    logHttp( resp )
    resp.raise_for_status()
except HTTPError as err:
    statusCode = err.response.status_code
    status = json.loads( err.response.content )[ 'errors' ][ 'code' ]
    print( f'Request error: GET /messages: Status Code:{ statusCode } { status } URL:{ err.response.url }' )
    print( f'Error: { err.response.content.decode( "utf-8" ) }' )
    sys.exit( 1 )
    
print( f'GET /messages: Messages count: { resp.json()[ "@total" ] }\n' )
input( 'Press Enter to continue...\n' )

# Extract the Message field from the response
messages = resp.json()[ 'Message' ] 

# If there are < 2 messages, Message will be a singleton, not a list, 
# so stuff it into a list to making parsing consistent
if not isinstance( messages, list ): messages = [ messages ]

# Delete all the messages in the inbox
for message in messages:
    try:
        resp = userSession.delete( 
            f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/messages/{ message[ "MsgId" ] }' )
        logHttp( resp )
        resp.raise_for_status()
    except HTTPError as err:
        statusCode = err.response.status_code
        status = json.loads( err.response.content )[ 'errors' ][ 'code' ]
        print( f'Request error: DELETE /messages: Status Code:{ statusCode } { status } URL:{ err.response.url }' )
        print( f'Error: { err.response.content.decode( "utf-8" ) }' )
        sys.exit( 1 ) 

print( f'DELETE /messages: Success\n' )
input( 'Press Enter to continue...\n' )

# Delete the user we just created, using the Admin credentials/session
try:
    resp = adminSession.delete( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/users/{ userObjectId }' )
    logHttp( resp )
    resp.raise_for_status()
except HTTPError as err:
    statusCode = err.response.status_code
    status = json.loads( err.response.content )[ 'errors' ][ 'code' ]
    print( f'Request error: DELETE /users: Status Code:{ statusCode } { status } URL:{ err.response.url }' )
    print( f'Error: { err.response.content.decode( "utf-8" ) }' )
    sys.exit( 1 ) 

print( f'DELETE /users: Success\n' )