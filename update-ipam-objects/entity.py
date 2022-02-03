import os
import sys
import requests
import ipaddress
import json
from BAM import BAM
import time
from RANGE import RANGE

bam_objs =  { "config": "Configuration", "network": "IP4Network", "block": "IP4Block", "users": "User", "ip": "IP4Address", 
    "server": "Server",
    "view": "View",
    "acls": "Acl",
    "tags": "Tag",
    "ranges": "DHCP4Range", "dhcp-roles": "DHCPDeploymentRole", "dhcp-options": "DHCPV4ClientOption",
    "dns-roles": "DNSDeploymentRole", "dns-options": "DNSOption" }

main_keys =  { 
    "Configuration": [ "name" ], 
    "View": [ "name", "id"],
    "Tag": [ 'name' ],
    "IP4Network": [ "CIDR", "(", "name", ")", "Gateway:", "gateway" ], 
    "IP4Block": [ "CIDR", "(", "name", ")" ], 
    "IP4Address": [ "address", "state", "(", "macAddress", ")", "-", "leaseTime" ], 
    "Zone": [ "absoluteName", "(", "id", ")" ],
    "DHCP4Range": [ "start", "-", "end" ], 
    "DHCPClient": [ 'name', 'value' ], 
    "DHCPService": [ "name", "value" ],
    "ACL": [ 'name' , 'aclValues'],
    "Server": [ "name", "defaultInterfaceAddress" ], 
    "NetworkServerInterface": [ "name", "(", "defaultInterfaceAddress", ")" ],
    "DNS": [ "name", "value" ], 
    "MASTER": [ "service", "type" ], 
    "SLAVE": [ "service", "type"], 
    "SLAVE_STEALTH": [ "service", "type"], 
    "STUB": [ "service", "type" ], 
    "FORWARDER" : [ "service", "type" ] , 
    "MASTER_HIDDEN": [ "service", "type" ],
    "HostRecord": ["absoluteName"] }

update_method = { 
    'DNS': "updateDNSDeploymentOption", 
    'DHCPService': 'updateDHCPServiceDeploymentOption', 
    'DHCPClient': 'updateDHCPClientDeploymentOption',
    'IP4Network': 'update',
    'IP4Block': 'update'
}
add_method = { 'range': 'addDHCP4Range', 'lease': 'addDHCPServiceDeploymentOption' }
add_keys = { 
    'range' : [ 'networkId', 'start', 'end', 'properties' ],
    'lease' : [ 'entityId', 'opt', 'value', 'properties' ],
}

DNSOptions = [ 
    "forwarding"
]

DHCPClientOptions = [
    "pxeclient",
    "boot-file-name",
    "domain-search",
    "domain-name",
    "dns-server",
    "ntp-server",
    "tftp-server",
    "tftp-server-name",
    "time-server",
    "time-offset",
    "avaya-ip-phones",
    "AudioCodes"
]

DHCPServerOptions = [
    "next-server",
    "filename",
    "ddns-domainname",
    "max-lease-time",
    "min-lease-time",
    "default-lease-time"
]

def redden(x): 
    return "\x1b[1;31;40m" + x + "\x1b[0m"

def printRed(x):
    print redden(x)

class entity():
    global update_method
    def __init__ (self, bam, call, args, method="GET"):
        self.bam = bam
        self.objs = []
        self.filtered = []
        self.filterflag = False
        ent = json.loads (self.bam.restCall(call, args, method=method)) 

        # Convert to an array in all cases
        if not isinstance(ent, list):
            ents = [ ent ]
        else:
            ents = ent
        if ents:
            self.type = ents[0]['type']
        for e in ents:
            thisobj = {}
            if e['id']:
                for key in e:
                    thisobj[key] = e[key]
                if e['properties']:
                    for p in e['properties'].split("|"):
                        if p:
                            attr, val = p.split("=")
                            thisobj[attr] = val
            else:
                thisobj['id'] = 0
            self.objs.append(thisobj)

    def attr(self, prop=None):
        if self.filterflag:
            if prop:
                return [ str(x[prop]) for x in self.filtered ]
            else:
                return [ str(x[main_keys[x['type']][0]]) for x in self.filtered ]
        else:
            if prop:
                return [ str(x[prop]) for x in self.objs ]
            else:
                return [ str(x[main_keys[x['type']][0]]) for x in self.objs ]

    def delete(self, obj=None):
        if obj != 'all':
            data = { "objectId" : obj['id'] }
            return self.bam.restCall('delete', data=data, method="DELETE")
        else:
            for r in self.objs:
                data = { "objectId" : r['id'] }
                return self.bam.restCall('delete', data=data, method="DELETE")
        
    def add(self, stype=None, name=None, eid=None):
        pid = str(self.attr('id')[0])
        #ptype = self.attr('type')[0]
        if stype == 'Zone':
            return entity(self.bam, 'addZone', 'parentId='+pid+'&absoluteName='+name +'&properties=deployable=true', method="POST")
        if stype in ['MASTER', 'SLAVE', 'FORWARDER', 'SLAVE_STEALTH', 'MASTER_HIDDEN']:
            return self.bam.restCall('addDNSDeploymentRole', 'entityId='+pid+'&serverInterfaceId='+eid +'&type=' + stype + '&properties=""', method="POST")
        else:
            print "add not implemented for stype: " + stype
            return

    def _get(self, x, stype=None, name=None):
        id = str(x['id'])
        if stype in [ 'IP4Network', 'IP4Block' ]:
            return  entity(self.bam, 'getIPRangedByIP', 'containerId='+str(id)+'&type='+stype+'&address='+str(name))
        if stype == 'IP4Address' and type(name) == str:
            return entity(self.bam, 'getIP4Address', 'containerId='+id+'&address='+name)
        if stype == 'Zone':
            return entity(self.bam, 'getZonesByHint', 'containerId='+id+'&start=0&count=10&options=hint='+name)
        elif stype == 'roles':
            if x['type'] in [ 'IP4Network', 'IP4Block', 'Zone']:
                return entity(self.bam, 'getDeploymentRoles', 'entityId='+id)
            if x['type'] == 'Server':
                    return entity(self.bam, 'getServerDeploymentRoles', 'serverId='+id)
        elif stype == 'options':
            return entity(self.bam, 'getDeploymentOptions', 'entityId='+id+'&optionTypes=DNSOption|DHCPV4ClientOption|DHCPServiceOption&serverId=0')
        elif stype == 'tags':
            return entity(self.bam, 'getLinkedEntities', 'entityId='+id+'&type=Tag&start=0&count=10')
        else:
            return entity(self.bam, 'getEntities', 'parentId='+id+'&type='+bam_objs[stype] + '&start=0&count=2000')

    def gets(self, stype=None, name=None):
        if self.filterflag:
            return [ self._get(x,stype, name) for x in self.filtered ]
        else:
            return [ self._get(x,stype, name) for x in self.objs ]

    def get(self, stype=None, name=None):
       id = str(self.attr('id')[0])
       ptype = self.attr('type')[0]
       if stype == 'IP4Address' and type(name) == str:
           return entity(self.bam, 'getIP4Address', 'containerId='+id+'&address='+name)
       if stype == 'Zone':
           return entity(self.bam, 'getZonesByHint', 'containerId='+id+'&start=0&count=10&options=hint='+name)
       if name:
           if type(name) == str:
               return entity(self.bam, 'getEntityByName', 'parentId='+id+'&type='+stype + '&name='+name)
           elif type(name) == int:
               return entity(self.bam, 'getEntityById', 'id='+str(name))
           else:
               print type(name)
       else: 
           if stype == 'roles':
               if ptype in [ 'IP4Network', 'IP4Block', 'Zone']:
                   return entity(self.bam, 'getDeploymentRoles', 'entityId='+id)
               if ptype == 'Server':
                   return entity(self.bam, 'getServerDeploymentRoles', 'serverId='+id)
           elif stype == 'options':
               return entity(self.bam, 'getDeploymentOptions', 'entityId='+id+'&optionTypes=DNSOption|DHCPV4ClientOption|DHCPServiceOption&serverId=0')
           elif stype == 'tags':
               return entity(self.bam, 'getLinkedEntities', 'entityId='+id+'&type=Tag&start=0&count=10')
           else:
               return entity(self.bam, 'getEntities', 'parentId='+id+'&type='+stype + '&start=0&count=2000')
 
    def _show(self, x):
        dstr = ''
        if x['id'] == 0:
            return dstr
        for key in main_keys[x['type']]:
            if key in x and x[key]:
                if type(x[key]) == int:
                    dstr += str(x[key]) + " " 
                else:
                    dstr += x[key].encode('utf-8') + " " 
            else:
                dstr += str(key) + ' '
        if x['type'] == 'IP4Address':
            fqdn = entity(self.bam, 'getLinkedEntities', \
                                   'entityId='+str(x['id'])+'&type=HostRecord&start=0&count=1')
            if len(fqdn.objs):
                dstr += fqdn.objs[0]['absoluteName']
        if 'serverInterfaceId' in x:
            dstr += self.get(name=x['serverInterfaceId']).show()
        if 'secondaryServerInterfaceId' in x:
            dstr += self.get(name=int(x['secondaryServerInterfaceId'])).show()
        return dstr

    def show(self, idx=999):
        if self.filterflag:
            if idx == 999:
                showstring = '\n'.join([self._show(x) for x in self.filtered])
            else:
                showstring = self._show(self.filtered[idx])
        else:
            if idx == 999:
                showstring = '\n'.join([self._show(x) for x in self.objs])
            else:
                showstring = self._show(self.objs[idx])
        if len(showstring) < 2:
            return redden("None")
        else:
            return showstring

    # Idea is to match a value to a property
    # If a property is not given the value is matched with the main key of the object type
    def _match(self, x, prop, val):
        # By default, we check the main key if no specific property is provided
        if not prop:
            prop = main_keys[x['type']][0]
        if prop in x and (val and x[prop] == val):
            return x

        if x['type'] in [ 'DNS', 'DHCPClient' , 'DHCPService']:
            if prop in x['name'] and (val and x['value'] == val):
                return x #self._show(x)
            elif prop in x['name'] and val == None:
                return x #self._show(x)
        else:
            if prop in x and (val and x[prop] == val):
                return x #self._show(x)
            elif prop in x and val == None:
                return x #self._show(x)
        
    def fc_count(self, prop, val=None):
        arr = (filter(None, [ self._match(x, prop, val) for x in self.objs ]))
        return len(arr)

    def filter(self, val, prop=None):
        self.filtered = filter(None, [ self._match(x, prop, val) for x in self.objs ])
        self.filterflag = True
        return self.show()

    def deploy(self):
        if self.objs[0]['type'] == 'Server':
            data = {
                "serverId": str(self.objs[0]['id']),
                "services": "services=DHCP"
            }
            res = self.bam.restCall('deployServerServices', data=data, method="POST")
            if res == 200:
                print 'deploying server: ' + self.attr('name')[0]
                while True:
                    time.sleep(4)
                    data = {
                        "serverId": str(self.objs[0]['id']),
                        "properties": ""
                    }
                    status = self.bam.restCall('getServerDeploymentStatus', data=data)
                    if status == '7':
                        print 'deployed successfuly'
                        break
                    elif status == 3:
                        print 'failed to deploy'
                        break
                    elif status == 5:
                        print 'warning while deploying' 
                        break
                    elif status == 4:
                        print 'not deployed'
                        break
                    elif status == 6:
                        print 'invalid error'
                        break
                    elif status == 2:
                        print 'cancelled deployment'
                        break
                    else:
                        print status
            else:
                print 'failed to deploy server: ' + self.attr('name')[0]

    def update(self, prop, val):
        for obj in self.objs:
            if obj['type'] in [ 'DNS', 'DHCPClient' , 'DHCPService']:
                if prop in obj['name'] and obj['value'] != val:
                    obj['value'] = str(val)
                    newobj = {}
                    for p in [ 'id', 'type', 'value', 'name', 'properties' ]:
                        newobj[p] = obj[p]
            if obj['type'] in [ 'IP4Network', 'IP4Block' ]:
                newobj = {}
                for p in ['id', 'type', 'name', 'properties']:
                    newobj[p] = obj[p]
                newobj[prop] = val
            res = self.bam.restCall(update_method[obj['type']], jsonflag=1, data=newobj, method="PUT")
            #if res == 'OK':
            #    print 'successfuly updated ' + prop

    def overlaps(self, start, end):               
        results = []
        if self.type == 'DHCP4Range':
            for e in self.objs:
                r = RANGE(e['start'], e['end'])
                if r.conflicts(start, end):
                    results.append(e)
            return results

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        return setattr(self, name, value)
        
