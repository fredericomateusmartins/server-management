#!/usr/bin/env python

# Red Hat Satellite 6 server registration

from getpass import getpass
from json import dumps
from os import system, WSTOPSIG
from readline import parse_and_bind
try:
    from requests import exceptions, get, post, put
except ImportError:
    print("""Needed libary 'python2-requests' missing, subscribe machine in Satellite for library install.
             # subscription-manager register --org=ORGANIZATION_NAME --activationkey=DEFAULT-KEY""")
    exit(-1)
from socket import gethostname
from sys import argv, path
from time import sleep
from types import MethodType

# Use library as a system module path for import 
path.insert(0, argv[1])

from library import Boolean, Interactive, Monitor, GetUser, GetSystemVersion, OutputWaiting


class Satellite(object):

    host = 'satellite.example.com'
    base = 'https://{}/api/v2/'.format(host)
    satellite = 'https://{}/katello/api/v2/'.format(host)
    certificate = '/etc/pki/ca-trust/source/anchors/katello-server-ca.pem'
    organization = 'ORGANIZATION_NAME'
    clustername = 'DEFAULT'
    force = ''

    def __init__(self):
        
        self.hostname = gethostname()
        
        self.GetUser()
        self.GetPassword()
        self.Preflight()
        self.Authenticate('Authenticating user {}'.format(self.username), False)

        self.json = JSON(self.username, self.password, self.certificate)
        
        #if not self.hostname[-31:] == 'example.com': # For puppet registration, if restricted by domain
        #    self.hostname = self.hostname + 'example.com'
        #    system('hostnamectl set-hostname {0}'.format(self.hostname))
            
    # Authentication
    def GetUser(self):

        self.username = GetUser(argv[7])

    def GetPassword(self):

        self.password = getpass(prompt="Network password: ")
    
    @OutputWaiting
    def Authenticate(self):
        
        if get(self.base, auth=(self.username, self.password), verify=self.certificate).json().get('error', None):
            sleep(2)
            return 1
        
        return 0

    # Prerequisites
    def Preflight(self):

        check = Monitor(self.host, self.hostname)

        check.Host('Name resolve and route', self.force)
        check.Port('HTTPS port connection', False, 443)
        self.puppet = check.Port('Puppet port connection', True, 8140)
        check.Katello('Red Hat Satellite 6 package', False)

    # API Verification
    @OutputWaiting
    def VerifyOrganization(self):

        try:
            self.orgjson = self.json.Get('{0}organizations/{1}'.format(self.satellite, self.organization))
            if not self.json.error:
                return 0
            
        except exceptions.SSLError:
            wait.Info('Certificate verification for host {} failed'.format(self.host))
        
        return 1

    @OutputWaiting
    def VerifyKey(self, clustername):
        
        self.clustername = clustername
        json = self.json.Get('{0}organizations/{1}/activation_keys?search={2}-key'.format(self.satellite, self.orgjson['id'], self.clustername))

        if self.json.error:
            return 1

        self.key_exists = False
        for key in json.get('results', None):
            if key['name'] == '{0}-KEY'.format(self.clustername):
                self.key_exists = True
                break

        return 0

    # API Calls
    @OutputWaiting
    def ListKeys(self):

        org = self.json.Get('{0}organizations/{1}'.format(self.satellite, self.organization))
        keys = self.json.Get('{0}organizations/{1}/activation_keys?per_page=100000'.format(self.satellite, org['id']))

        if self.json.error:
            return 1

        self.output = ["Available activation keys:\033[K"]
        for each in keys.get('results', None):
            self.output.append(each['name'][:-4])
        self.output = '{}\n{}'.format(self.output[0], '\n'.join(sorted(self.output[1:])))

        return 0

    @OutputWaiting
    def SimpleRegistration(self):
    
        version = GetSystemVersion()
        if version == 6:
            self.clustername = self.clustername + version
        
        exit_status = system('subscription-manager register --org={} --activationkey={}-KEY {} &> /dev/null'.format(
            self.organization, self.clustername, self.force))
        if WSTOPSIG(exit_status) == 64:
            wait.Info('System already registered, use --force to override')
            
        return exit_status

    def CreateNamespace(self):

        results = {}; results['subscriptions'] = []
    
        wait.Start('Product creation')
        
        results['product'] = self.json.Post("{}products/".format(self.satellite), dumps({"organization_id": self.orgjson['id'],
            "description": self.clustername, "name": "{}-PROD".format(self.clustername)}))

        wait.Stop(self.json.error)
        
        results['product'] = results['product']['id']
        
        wait.Start('Repository creation')

        results['repository'] = self.json.Post("{}repositories/".format(self.satellite), dumps({"organization_id": self.orgjson['id'],
           "name": "{}-REPO".format(self.clustername), "product_id": results['product'], "content_type": "yum"}))['id']

        wait.Stop()
        wait.Start('Activation key creation')

        results['key'] = self.json.Post("{}activation_keys/".format(self.satellite), dumps({"organization_id": self.orgjson['id'], 
            "name": "{}-KEY".format(self.clustername), "environment_id": 1, "content_view_id": 1, "unlimited_hosts": True}))['id']

        wait.Stop()
        wait.Start('Hosts subscriptions attachment')
        
        for each in self.json.Get('{}/organizations/{}/subscriptions?per_page=100000'.format(self.satellite, 
            self.orgjson['id'])).get('results', None):
            try:
                if each['name'] == '{}-PROD'.format(self.clustername):
                    self.json.Put("{}activation_keys/{}/add_subscriptions".format(self.satellite, "11"), # CI Activation Key
                        dumps({"id": 11, "subscriptions": [{"id": each['id']}]}))
                    results['subscriptions'].append({"id":each['id']})
                    continue
                
                if each['name'] == 'GSS-SERVICOS-PROD':
                    results['subscriptions'].append({"id":each['id']})
                    continue
                
                if each['host']['name'][:9] == 'virt-who-' and not 'Smart Management for Unlimited Guests' in each['name']:
                    results['subscriptions'].append({"id":each['id']})

            except KeyError:
                pass

        self.json.Put("{}activation_keys/{}/add_subscriptions".format(self.satellite, results['key']), 
            dumps({"id": results['key'], "subscriptions": results['subscriptions']}))

        wait.Stop()
        
        self.SimpleRegistration('Registration with created activation key', False)
        self.CollectionAppend('Host collections creation', self.force)

    @OutputWaiting
    def CollectionAppend(self):

        collections = self.json.Get('{}/organizations/{}/host_collections?per_page=100000'.format(self.satellite, self.orgjson['id']))
        if not self.json.error:
            for collection in collections.get('results', None):
                if collection['name'] == '{}-COLLECTION'.format(self.clustername):
                    break
            else:
                collection = self.json.Post("{}host_collections".format(self.satellite), dumps({"organization_id": self.orgjson['id'],
                "name": "{}-COLLECTION ".format(self.clustername)}))
                if self.json.error:
                    return 1

            host = self.json.Get('https://{}/api/hosts/{}'.format(self.host, self.hostname))
            if self.json.error:
                return 1
                
            self.json.Put("{}host_collections/{}/add_hosts".format(self.satellite, collection['id']),
                dumps({"host_ids": host['id']}))

            if not self.json.error:
                return 0
        return 1

    @OutputWaiting
    def PuppetRegistration(self):

        return system('puppet agent -t > /dev/null')

    @OutputWaiting
    def PuppetClass(self, pclass):
        
        system('systemctl restart puppet')

        host = self.json.Get('https://{}/api/hosts/{}'.format(self.host, self.hostname))
        puppet = self.json.Get('https://{}/api/puppetclasses/{}'.format(self.host, pclass))
        
        if self.json.error:
            puppet = self.json.Post("https://{}/api/v2/puppetclasses/".format(self.host),
                dumps({"puppetclass": {"name": pclass.lower()}}))

        if str(host['name']) == self.hostname and not self.json.error:
            self.json.Put("https://{}/api/hosts/{}".format(self.host, host['id']),
                dumps({"id": host['id'], "host": {"puppetclass_ids": puppet['id']}}))
            if not self.json.error:
                return 0

        return 1
        
    @OutputWaiting
    def Hostgroup(self):
        
        hostgroup = self.json.Get('https://{}/api/v2/hostgroups?search={}'.format(self.host, self.clustername))
        
        if self.json.error:
            hostgroup = self.json.Post("https://{}/api/v2/hostgroups/".format(self.host),
                dumps({"hostgroup": {"name": self.clustername}}))
        
        
class JSON(object):

    def __init__(self, username, password, certificate):

        self.username = username
        self.password = password
        self.certificate = certificate

    def __getattribute__(self, attribute):
        
        if not attribute == 'error':
            self.error = False
        return object.__getattribute__(self, attribute)

    def Get(self, location):

        result = get(location, auth=(self.username, self.password), verify=self.certificate).json()

        if result.get('error', None):
            wait.Info('{}'.format(result['error']['message']))
            self.error = True

        return result

    def Post(self, location, json_data):

        result = post(location, data=json_data, auth=(self.username, self.password), verify=self.certificate, 
            headers={'content-type': 'application/json'}).json()
        
        if result.get('errors', None):
            wait.Info('Namespace is being created in another machine. Wait for completion and re-run the command') # Conflicting product in Satellite
            wait.Info('If no other machine is creating the namespace, delete the product manually in https://{0}/'.format(Satellite.host))
            self.error = True

        return result

    def Put(self, location, json_data):

        result = put(location, data=json_data, auth=(self.username, self.password), verify=self.certificate, 
            headers={'content-type': 'application/json', 'accept':'application/json,version=2'}).json()
        
        if result.get('errors', None):
            wait.Info('{}\033[K'.format(result.get('errors', None)[0]))
            wait.Warning('A physical subscription was already attached, others might have been skipped\033[K')
        elif result.get('error', None):
            wait.Info('{}\033[K'.format(result.get('error', None)))
            self.error = True
            
        return result


wait = OutputWaiting()
API = Satellite()

if argv[5] == 'true':
    API.force = '--force'

if argv[2] == 'true':
    API.ListKeys('Fetching data from Satellite', False)
    print(API.output)
    exit()

if argv[3] == 'true':
    if argv[8] == 'true':
        API.clustername = 'EXTERNAL'
    API.SimpleRegistration('Simple registration without custom repositories', API.force)
else:
    API.VerifyOrganization('Verify organization existence', False)
    clustername = Interactive(argv[4], 'Project name?', gethostname().split('.')[0][4:-2]).upper()
    API.VerifyKey('Verify activation key existence', True, clustername)
    if not API.key_exists and Boolean(argv[5], 'Activation key does not exist, create it?'):
        API.CreateNamespace()
    else:
        API.SimpleRegistration('Satellite 6 server registration', False)
        API.CollectionAppend('Host collections registration', API.force)
        
if not API.puppet and (argv[6] == 'true' or raw_input("Puppet agent registration ? [y/N] ") == 'y'):
    API.PuppetRegistration('Puppet registration', False)
    API.PuppetClass('Include Puppet class rpmupdater', API.force, 'rpmupdater')
    if 'TEMPLATE' not in API.clustername:
        API.PuppetClass('Create Puppet class project', API.force, API.clustername)