import sys
import base64
from BAM import BAM
from entity import entity

def usage():
    print ('usage: python update_block.py <a.b.c.d/8> <new_name>')
    sys.exit()

#bam_ip = "10.201.128.158"   #PROD
bam_ip = "10.101.66.232"     #LAB
#bam_user = "username@mfcgd.com"     #    <- update this to your username
bam_user = "chanalt@mfcgd.com"     #    <- update this to your username
bam_pwd = base64.b64decode(open(".secret").read().split()[0].decode("utf-8"))     # needs your base64-hashed password in a file ".secret"
conf_name = ".Manulife Global"
view_name = "Internal"

# Arguments taken from input
try:
    block = sys.argv[1]
    cidr, nask = sys.argv[1].split('/')
    new_name = sys.argv[2]
except Exception as e:
    usage()

try:
    bam = BAM(bam_ip, bam_user, bam_pwd)
    bam.login()
    config = entity(bam, 'getEntityByName', 'parentId=0&type=Configuration&name=' + conf_name)

    blk = entity(bam, 'getIPRangedByIP', 'containerId='+str(config.attr('id')[0])+'&type=IP4Block&address='+str(cidr))
    if not blk.objs:
        raise Exception("Block " + block + " does not exist")

    if blk.attr('CIDR')[0] != block:
        raise Exception("Block " + block + " does not exist")

    print blk.show()    
    blk.update('name', new_name)
    print ('successfuly updated block   : ' + block + ' with name : ' + new_name)


except Exception as e:
    print ("Exception: " + str(e))
