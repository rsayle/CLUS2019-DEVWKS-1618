import requests
import json
from base64 import b64encode
import time

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
TEMPLATE = 'Interface Description'
TARGET_BY_ID = 'MANAGED_DEVICE_UUID'
DEPLOY_INIT = 'INIT'
DEPLOY_SUCCESS = 'SUCCESS'

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
    return result['response'][0]['id']

def get_template(dnac, token, template_name):
    # get all templates
    resource = '/api/v2/template-programmer/template'
    url = '%s%s' % (dnac, resource)
    hdrs = {}
    hdrs['Content-Type'] = CTYPE
    hdrs['X-Auth-Token'] = token
    response = requests.request(GET,
                                url,
                                headers=hdrs,
                                verify=VERIFY,
                                timeout=TIMEOUT)
    templates = json.loads(response.text)
    # find the named template
    versioned_template = ''
    for template in templates:
        if template['name'] == template_name:
            # find the versioned template
            last_version = 0
            template_versions = template['versionsInfo']
            for template_version in template_versions:
                if int(template_version['version']) > last_version:
                    last_version = int(template_version['version'])
                    versioned_template = template_version['id']
    return versioned_template

def deploy_template(dnac, token, target, template, parameters):
    resource = '/api/v2/template-programmer/template/deploy'
    url = '%s%s' % (dnac, resource)
    hdrs = {}
    hdrs['Content-Type'] = CTYPE
    hdrs['X-Auth-Token'] = token
    tgt_info = {
                'type': TARGET_BY_ID,
                'id': target,
                'params': parameters
               }
    target_info = [tgt_info]
    data = {
            'templateId': template,
            'targetInfo': target_info
           }
    data = json.dumps(data)
    response = requests.request(POST,
                                url,
                                headers=hdrs,
                                data=data,
                                verify=VERIFY,
                                timeout=TIMEOUT)
    return json.loads(response.text)['response']['taskId']

def check_task(dnac, token, task):
    resource = '/api/v1/task/'
    url = '%s%s%s' % (dnac, resource, task)
    hdrs = {}
    hdrs['Content-Type'] = CTYPE
    hdrs['X-Auth-Token'] = token
    response = requests.request(GET,
                                url,
                                headers=hdrs,
                                verify=VERIFY,
                                timeout=TIMEOUT)
    progress = json.loads(response.text)['response']['progress']
    progress_fields = progress.split(':')
    deployment = progress_fields[len(progress_fields)-1]
    return deployment

def check_deployment(dnac, token, deployment):
    resource = '/api/v1/template-programmer/template/deploy/status/'
    url = '%s%s%s' % (dnac, resource, deployment)
    hdrs = {}
    hdrs['Content-Type'] = CTYPE
    hdrs['X-Auth-Token'] = token
    response = requests.request(GET,
                                url,
                                headers=hdrs,
                                verify=VERIFY,
                                timeout=TIMEOUT)
    status = json.loads(response.text)['status']
    return status

# main ################################################################################################################

# get an x-auth-token
token = get_token(DNAC, USER, PASSWD)

# find the target device's UUID
switch = get_switch(DNAC, token, HOSTNAME)

# find the committed template's UUID
template = get_template(DNAC, token, TEMPLATE)

# build the template parameter values
parameters = {}
parameters['interface'] = '<switch_interface>'
parameters['description'] = '<interface_description>'

# deploy the template
task = deploy_template(DNAC, token, switch, template, parameters)

print('Waiting three seconds for the task to complete...')
time.sleep(3)

# get the deployment from the task details
deployment = check_task(DNAC, token, task)

# monitor the deployment job until complete
status = check_deployment(DNAC, token, deployment)
while status == DEPLOY_INIT:
    print ('Template deployment still running...')
    status = check_deployment(DNAC, token, deployment)
    time.sleep(3)

if status == DEPLOY_SUCCESS:
    print('Template pushed successfully.  Check your assigned interface to verify the results.')
else:
    print('Template push failed.  Please ask the proctor for help.  Failure code = %s' % status)
