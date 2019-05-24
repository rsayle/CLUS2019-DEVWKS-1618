from dnac import Dnac
from dnac.networkdevice import NetworkDevice
from dnac.template import Template, TARGET_BY_ID

# connect to DNAC
dnac = Dnac()

# get the switch's UUID
switch = NetworkDevice(dnac, 'leaf2.abc.inc')

# load the template
template = Template(dnac, 'Interface Description')

# set the template's target
template.target_id = switch.get_id_by_device_name(switch.name)
template.target_type = TARGET_BY_ID

# input the template parameters
template.versioned_template_params['interface'] = 't1/0/10'
template.versioned_template_params['description'] = 'Configured by exercise 5.4'

# push the template
template.deploy_sync(3)

print('Done pushing the template. Check your assigned switchport\'s configuration.')
