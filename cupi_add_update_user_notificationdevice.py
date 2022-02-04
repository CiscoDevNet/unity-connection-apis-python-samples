'''
Cisco Unity Connection add/update user notification device using the CUPI.

Creates a test user then updates details for the user's default SMTP
notification device.

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

from ssl import SSLError
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

# Edit .env file to specify your CUC hostname and user credentials
from dotenv import load_dotenv
load_dotenv( override = True )

# Enable detailed HTTP/XML logging in .env
DEBUG = os.getenv( 'DEBUG' ) == 'True'

def logHttp( response ):
    if not DEBUG == True: return
    print( '--------------- Request/Response ---------------' )
    print(
        dump.dump_all(
            response = response,
            request_prefix = None,
            response_prefix = None
        ).decode( 'utf-8', errors='ignore' ), '\n' )

# Create a requests.Session to enable default parameters,
# cookies and persistent HTTP connections
session = requests.Session()

# Download the CUCM 'tomcat' PEM format certificate via 
# CUCM OS Administration -> Security -> Certificate Management and 
# place it in the root directory of this project.
# Configure the certificate location .env

# If the CUC tomcat cert is configured in .env
if os.getenv( 'CUC_CERT' ):
    session.verify = os.getenv( 'CUC_CERT' )
# else disable certificate checking (not for production)
else:
    session.verify = False

# CUC self-signed certs do no have a (deprecated) subjectAltName.
# Disable the warning.
urllib3.disable_warnings( urllib3.exceptions.SubjectAltNameWarning )

# Create a Basic Auth encoded credential
adminCredentials = HTTPBasicAuth( os.getenv( 'APP_USER' ), os.getenv( 'APP_PASSWORD' ) )

# Retrieve the list of available MailboxStores
try:
    resp = session.get( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/mailboxstores',
        headers = { 'Accept': 'application/json' },
        auth = adminCredentials )
    # Raise an exception if a non-200 HTTP response received
    logHttp( resp )
    resp.raise_for_status()
except HTTPError as err:
    statusCode = err.response.status_code
    print( f'Request error: POST /user Status Code:{ statusCode } URL:{ err.response.url }' )
    print( f'Error: { err.response.content.decode( "utf-8" ) }' )
    if statusCode == 400:
        print( '-->Hint: this error may be due to existing duplicate alias/extension.\n' )
    sys.exit( 1 )

mailboxStores = resp.json()[ 'MailboxStore' ]

# If there are < 2 mailbox stores, mailboxStores will be a singleton, not a list,
# so stuff it into a list to making parsing easier
if not isinstance( mailboxStores, list ): mailboxStores = [ mailboxStores ]

# Parse the ObjectId of the first mailbox store in the list
mailboxStoreId = mailboxStores[ 0 ][ 'ObjectId' ]

print( f'GET /mailboxstores: ObjectId: { mailboxStoreId }\n' )
input( 'Press Enter to continue...\n' )

# Create a new test user with extension 987654321
req = {
    "Alias": "testUser",
    "DtmfAccessId": "987654321"
}

# Note: templateAlias must be provided in URL query parameters
try:
    resp = session.post( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/users',
        params = { 'templateAlias': 'voicemailusertemplate' },
        headers = { 'Content-Type': 'application/json' },
        auth = adminCredentials,
        json = req )
    logHttp( resp )
    resp.raise_for_status()
except HTTPError as err:
    statusCode = err.response.status_code
    print( f'Request error: POST /user Status Code:{ statusCode } URL:{ err.response.url }' )
    print( f'Error: { err.response.content.decode( "utf-8" ) }' )
    if statusCode == 400:
        print( 'This error may be due to existing duplicate alias/extension.\n' )
    sys.exit( 1 )

# Parse the new user's ObjectId from the end of the Location header URL
userObjectId = resp.headers[ 'Location' ].split( '/' )[ -1 ]

print( f'POST /users: ObjectId: { userObjectId }\n' )

input( 'Press Enter to continue...\n' )

# The new user will have a default SMTP notification device.
# This device has no specific configuration details and is disabled.
# Retrieve the user's SMTP device list
try:
    resp = session.get( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/users/{ userObjectId }/notificationdevices/smtpdevices',
        headers = { 'Accept': 'application/json' },
        auth = adminCredentials )
    logHttp( resp )
    resp.raise_for_status()
except Exception as err:
    print( f'Request error: GET /smtpdevices: { err }\n' )
    sys.exit( 1 )

# Parse the device ObjectId from the first device in the list
deviceObjectId = resp.json()[ 'SmtpDevice' ][ 'ObjectId' ]

print( f'GET smtpdevices: ObjectId: { deviceObjectId }\n' )

input( 'Press Enter to continue...\n' )    

# Update the device to enable it and set the To: email destination
req = {
    "Active": True,
    "SmtpAddress": "user@abc.inc"
}

try:
    resp = session.put( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/users/{ userObjectId }/notificationdevices/smtpdevices/{ deviceObjectId }',
        headers = { 'Content-Type': 'application/json' },
        auth = adminCredentials,
        json = req
        )
    logHttp( resp )
    resp.raise_for_status()
except Exception as err:
    print( f'Request error: PUT /smtpdevices: { err }\n' )
    sys.exit( 1 )

print( f'PUT /smtpdevices: Success\n' )
input( 'Press Enter to continue...\n' )       

# Delete the user we just created
try:
    resp = session.delete( 
        f'https://{ os.getenv( "CUC_HOSTNAME" ) }/vmrest/users/{ userObjectId }',
        auth = HTTPBasicAuth( os.getenv( 'APP_USER' ), os.getenv( 'APP_PASSWORD' ) ),
        headers = { 'Accept': 'application/json' }
        )

    # Raise an exception if a non-200 HTTP response received
    resp.raise_for_status()
    
except Exception as err:
    print( f'Request error: DELETE /users: { err }\n' )
    sys.exit( 1 )

print( f'DELETE /users: Success' )