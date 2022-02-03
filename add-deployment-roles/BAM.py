import requests
import json
from requests.auth import HTTPBasicAuth
import base64

#NOTE : YOU MAY NEED TO pip install requests

class BAM():

    def __init__ (self, ip, user, pswd):
    	self.url = 'http://' + ip + '/Services/REST/v1/' 
    	self.username = user
    	self.password = pswd
    	self.confid = 0
    	self.headers = {}
        self.debug = 0

    def debugOn (self):
        self.debug = 1

    def debugOff(self):
        self.debug = 0

    def login(self):
        url = self.url + 'login?username=' + self.username + '&password=' + self.password
        response = requests.get(url)
	elements = str(response.text).split(' ')
        self.headers = { "Authorization" :  elements[2] + " " +  elements[3] }
        if self.debug:
            print 'Authorization header: ' + str(self.headers)

    def update(self, entity):
	url = self.url + 'update'
	headers = self.headers.update({ "Content-Type": "application/json" })
	response = requests.put(url, headers=self.headers, data=json.dumps(entity))
	if response and 'do not have access' in response:
		raise Exception('No access')
	if not response:
		raise Exception('No access')
	
    def restCall(self, call, data, jsonflag=0, method="GET"):
	url = self.url + call
	if jsonflag:
		headers = self.headers.update({ "Content-Type": "application/json" })
		if method == "GET":
			response = requests.get(url, headers=self.headers)
		elif method == "POST":
			response = requests.post(url, jsonflag=data, headers=self.headers)
                elif method == "PUT":
			response = requests.put(url, data=json.dumps(data), headers=self.headers)
	else:
		params = data
		if method == "GET":
			response = requests.get(url, params=data, headers=self.headers)
		elif method == "POST":
			response = requests.post(url, params=data, headers=self.headers)
                elif method == "DELETE":
			response = requests.delete(url, params=data, headers=self.headers)

	if(response.status_code == 200) and method == "GET":
		if not response.content:
			raise Exception('no access')
		else:
                        if self.debug:
                            print 'Response: ' + str(response.content)
		    	return response.content
        elif method == "POST":
                return response.status_code
	elif (response.status_code == 200) and method == 'PUT':
                if self.debug:
                    print 'Response: ' + str(response.content)
                return "OK"
        else:
		return response.status_code
		#raise Exception(response.reason)

    def getConf(self, val):
	response = self.restCall('getEntityByName', 'parentId=0&type=Configuration&name=' + val)
	self.confid = json.loads(response)["id"]


    def getEntity (self, type, val):
	if (type == 'ip'):
		return entity(self, val, 'IP4Address')
	if (type == 'mac'):
		return entity(self, val, 'MACAddress')

class entity:
    def __init__ (self, bam, val, etype, copyobj=0):
	self.bam = bam
	self.values = {}
	self.properties = {}
	obj = {}
	
	self.objprefix = ""
	if etype =='IP4Address':
		self.objprefix = "ip_"
	if etype =='MACAddress':
		self.objprefix = "mac_"
	if etype =='HostRecord':
		self.objprefix = "host_"
	if etype =='Tag':
		self.objprefix = "tag_"

	#if not val:
	#	return obj

	# If value is zero, we return an empty entity object with id=0 and an empty propstr
	if val==str(0) or val==0:
		return self


	# If type was provided, We get the object based on the type.	
	# If type was not provided, we instantiate the object using the value passed in. 
	# This is when getLinkedEntity calls this to instantiate an object
	if copyobj==0:
		ent = self.bam.restCall('searchByObjectTypes', 'keyword='+val+'&types='+etype+'&start=0&count=1')
		if len(json.loads(ent)):
			obj = json.loads(ent)[0]
		else:
			return 
	else:
		obj = json.loads(val)[0]

	for key in obj:
		if obj[key]:
			if key != "properties":
				self.values[self.objprefix + key] = obj[key]
			else:
				self.properties = obj[key]

	# If properties exists, split the properties and load them into values
	if (self.properties):
		keyvals = self.properties.split('|')
		for attr in keyvals:
			if len(attr) > 1 :
				key, val = attr.split("=")
				self.values[self.objprefix + key] = val


    def getProperty(self, type):
	prop = self.propstr.split(type+'=')
	if len(prop) > 1:
		return prop[1].split('|')[0]
	else:
		return str(0)

    def getLinkedEntity(self, etype):
	res = 0
	response = self.bam.restCall('getLinkedEntities', 'entityId='+str(self.values[self.objprefix+"id"])+'&type='+etype+'&start=0&count=1')

	if "not supported" in str(response):
		return self
	
	if type(response)!='str' and len(json.loads(response)):
		return entity(self.bam, response, etype, 1)
	else:
		return self

class tag(entity):
    name = ""
    def __init__ (self, bam, val, type=0):

	if not type:
		tagobj = entity.__init__(self, bam, val, 'Tag')
	else:
		tagobj = entity.__init__(self, bam, val)

	if tagobj.id:
		self.name = val["name"]

class mac(entity):
    vendor = ""
    def __init__ (self, bam, val, type=0):

	if not type:
		macobj = entity.__init__(self, bam, val, 'MACAddress')
	else:
		macobj = entity.__init__(self, bam, val)

	if macobj.id:
		self.vendor = self.getProperty('macVendor')


class ip(entity):
    mac = 0
    lease = 0
    state = "STATIC"

    def __init__ (self, bam, val):
	ipobj = entity.__init__(self, bam, val, 'IP4Address')
	if ipobj.id:
		self.mac = self.getProperty('macAddress')
		self.lease = self.getProperty('leaseTime')
		self.state = self.getProperty('state')

    def getMAC(self):
	res = self.bam.restCall('getLinkedEntities', 'entityId='+str(self.id)+'&type=MACAddress&start=0&count=1')
	if res:
		return json.loads(res)[0]
	

    def getHostname(self, bam):
	hostname = ""
	res = bam.restCall('getLinkedEntities', 'entityId='+str(self.id)+'&type=HostRecord&start=0&count=1')
	if res:
		hostname = json.loads(res)[0]["properties"]
	
	return hostname

			

