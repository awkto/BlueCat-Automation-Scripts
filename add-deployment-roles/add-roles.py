import sys
from BAM import BAM
from entity import entity

def usage():
    print ('usage: python add_roles.py <zone_name> <MASTER|SLAVE|FORWARDER|MASTER_HIDDEN|SLAVE_STEALTH> <server_fqdn>')
    sys.exit()

#bam_ip = "10.101.66.232" #ddi-lab
#bam_ip = "10.201.128.158" #prod_bam
#bam_ip = open(".secret").read().splitlines()[0] #variable

from config import *
bam_ip = BAM_IP
bam_user = BAM_USER
conf_name = CONFIG_NAME
view_name = VIEW_NAME

#bam_user = "chanalt@mfcgd.com"
#bam_user = open(".userid").read().splitlines()[0] #variable
bam_pwd = "$(cat .secret | base64 --decode)"
#conf_name = ".Manulife Global"
#view_name = "Internal"

# Arguments taken from input
try:
    zone_name = sys.argv[1]
    role_type = sys.argv[2]
    server_fqdn = sys.argv[3]
except Exception as e:
    usage()

try:
    bam = BAM(bam_ip, bam_user, bam_pwd)
    bam.login()
    config = entity(bam, 'getEntityByName', 'parentId=0&type=Configuration&name=' + conf_name)
    view = config.get('View', view_name)
    zone = view.get('Zone', zone_name)
    servers = config.get('Server')
    server = servers.filter(server_fqdn, 'fullHostName')
    if not servers.filtered:
        raise Exception("Server fqdn " + server_fqdn + " is not associated with any server")

    interfaces = servers.get('NetworkServerInterface')
    if not interfaces.objs:
        raise Exception("Could not get entity id for Server fqdn " + server_fqdn)

    res = zone.add(role_type, eid=interfaces.attr('id')[0])
    if res == 200:
        print "Added role: " + role_type + " " + server_fqdn
    else:
        raise Exception("Failed to add role: " + role_type + " " + server_fqdn)

except Exception as e:
    print ("Exception: " + str(e))
