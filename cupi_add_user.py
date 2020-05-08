'''
Cisco Unity Connection add user script using the CUPI API.

Creates a test user, then deletes the user.

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

from flask import Flask, request
import requests
from requests.auth import HTTPBasicAuth
import logging
from http.client import HTTPConnection
import os
import sys
import textwrap

# Edit .env file to specify your Webex integration client ID / secret
from dotenv import load_dotenv
load_dotenv()

# Change to true to enable request/response debug output
DEBUG = True

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

# Create a basic new user
req = {
    'Alias': 'testUser1',
    'DtmfAccessId': '987654321'
}

try:
    resp = requests.post( 
        f'https://{ os.getenv( "CUC_ADDRESS" ) }/vmrest/users?templateAlias=voicemailusertemplate',
        auth=HTTPBasicAuth( os.getenv( 'APP_USER' ), os.getenv( 'APP_PASSWORD' ) ),
        json = req,
        verify = False
        )

    # Raise an exception if a non-200 HTTP response received
    resp.raise_for_status()
    
except Exception as err:
    print( f'Request error: POST ../users: { err }' )
    sys.exit( 1 )
else:
    userId = resp.headers['Location'].split( '/' )[ -1 ]

    print( f'\n POST ../users: Created user Id: { userId }\n' )

input( 'Press Enter to continue...' )

# Delete the user we just created

try:
    resp = requests.delete( 
        f'https://{ os.getenv( "CUC_ADDRESS" ) }/vmrest/users/{ userId }',
        auth=HTTPBasicAuth( os.getenv( 'APP_USER' ), os.getenv( 'APP_PASSWORD' ) ),
        verify = False
        )

    # Raise an exception if a non-200 HTTP response received
    resp.raise_for_status()
    
except Exception as err:
    print( f'Request error: DELETE ../users: { err }' )
    sys.exit( 1 )
else:
    print( f'\n DELETE ../users/{ userId }: Success\n' )