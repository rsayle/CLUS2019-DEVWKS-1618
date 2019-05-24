import requests
import json
from pprint import pprint
from base64 import b64encode

# globals
CTYPE = 'application/json'
POST = 'POST'
GET = 'GET'
VERIFY = False
TIMEOUT = 5
DNAC = 'https://10.10.20.85'
USER = 'admin'
PASSWD = 'Cisco1234!'
HOSTNAME = 'leaf2.abc.inc'

def get_token(dnac, user, passwd):
    resource = '/dna/system/api/v1/auth/token'
    url = '%s%s' % (dnac, resource)
    credstr = '%s:%s' % (user, passwd)
    cred64 = b64encode(credstr.encode())
    cred64 = cred64.decode()
    creds = 'Basic %s' % cred64
    hdrs = {}
    hdrs['Authorization'] = creds
    hdrs['Content-Type'] = CTYPE
    response = requests.request(POST,
                                url,
                                headers=hdrs,
                                verify=VERIFY,
                                timeout=TIMEOUT)
    return str(json.loads(response.text)['Token'])

def get_switch(dnac, token, hostname):
    resource = '/api/v1/network-device'
    filter = '/?hostname=%s' % hostname
    url = '%s%s%s' % (dnac, resource, filter)
    hdrs = {}
    hdrs['Content-Type'] = CTYPE
    hdrs['X-Auth-Token'] = token
    response = requests.request(GET,
                                url,
                                headers=hdrs,
                                verify=VERIFY,
                                timeout=TIMEOUT)
    result = json.loads(response.text)
    return result

# main ################################################################################################################

# get an x-auth-token
token = get_token(DNAC, USER, PASSWD)

# find the target device's UUID
switch = get_switch(DNAC, token, HOSTNAME)

# print the results
pprint(switch)
