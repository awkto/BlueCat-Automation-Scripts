import sys
from BAM import BAM
from entity import entity

#Version 1.1

from config import *
bam_ip = BAM_IP
bam_user = BAM_USER
conf_name = CONFIG_NAME
view_name = VIEW_NAME

def usage():
    print ('usage: python clear_roles.py <zone_name>')
    sys.exit()

#bam_ip = "10.244.85.91"
#bam_user = "$(cat .username)"
bam_pwd = "$(cat .secret|base64)"
#conf_name = ".Manulife Global"
#view_name = "Internal"
zone_name = ""

# Arguments taken from input
try:
    zone_name = sys.argv[1]
except Exception as e:
    usage()

try:
    bam = BAM(bam_ip, bam_user, bam_pwd)
    bam.login()
    config = entity(bam, 'getEntityByName', 'parentId=0&type=Configuration&name=' + conf_name)
    if config.attr('id')[0] == str(0):
        raise Exception ("Configuration " + conf_name + " does not exist")
    view = config.get('View', view_name)
    if view.attr('id')[0] == str(0):
        raise Exception ("View: " + view_name + " does not exist ")
    zone = view.get('Zone', zone_name)
    if len(zone.objs) == 0:
        raise Exception ("Zone " + zone_name + " does not exist")
    roles = zone.get('roles')
    if len(roles.objs) == 0:
        raise Exception ("Roles dont exist on this zone")
    roles.delete('all')
    print ('Cleared all roles for zone:' + zone_name)

except Exception as e:
    print ("Exception: " + str(e))
