#!/usr/bin/env python

# Centreon alarm and monitoring configuration

from getpass import getpass
from paramiko import AutoAddPolicy, SSHClient, ssh_exception
from socket import gethostbyname, gethostname
from sys import argv, path
from time import sleep

# Use library as a system module path for import
path.insert(0, argv[1])

from library import Monitor, GetUser, OutputWaiting

if argv[4] == 'true':
    poller = 'OaM_Poller'
else:
    poller = 'Cloud_Poller'

ini = '''\
[{0}]
type = host
action = add
alias = {0}
ip = {1}
group = linux-servers
template = linux
resource = Team-Name
poller = OaM_Poller
snmp_community = RANDOM_STRING
snmp_version = 2c

[Team-Name]
type = resource
action = reload

[{2}]
type = poller
action = restart\
'''.format(gethostname().split('.')[0], gethostbyname(gethostname()), poller)


class SSH(object):

    proxy = None

    def __init__(self, host, user, password=None, port=22):

        self.host = host
        self.port = port
        self.user = user
        self.password = password or getpass(prompt="Network password: ")

    def forward(self, host, user=None, password=None, port=22):

        self._proxy = SSHClient()
        user = user or self.user
        password = password or self.password

        self._proxy.set_missing_host_key_policy(AutoAddPolicy())

        try:
            self._proxy.connect(host, port=port, username=user, password=password)
        except ssh_exception.AuthenticationException:
            print("Error: Authentication failed for user {0}".format(self.user))
            exit(-1)

        transport = self._proxy.get_transport()
        self.proxy = transport.open_channel("direct-tcpip", (self.host, self.port), (host, port))

    def execute(self, command):

        if not hasattr(self, '_ssh'):
            self._ssh = SSHClient()
            self._ssh.set_missing_host_key_policy(AutoAddPolicy())
            self._ssh.connect(self.host, username=self.user, password=self.password, sock=self.proxy)

        return self._ssh.exec_command(command)

    def close(self):

        if hasattr(self, '_ssh'):
            self._ssh.close()

        if hasattr(self, '_proxy'):
            self._proxy.close()


wait = OutputWaiting()

try:
    if argv[3] != 'false':
        with open(argv[3], 'r') as openini:
            ini = openini.read()
except IOError:
    wait.Error("No such file {0}".format(argv[3]))
    raise SystemExit

centreon = SSH('centreon.example.com', GetUser(argv[2]))
centreon.forward('satellite.example.com')

Monitor('satellite.example.com', gethostname().split('.')[0]).Port('Satellite SSH connection', False, 22)

wait.Start('Transfering .ini file to Centreon')
remoteini = '/path/to/centreon-orchestration/playbooks/{0}_default.ini'.format(gethostname())
stdin, stdout, stderr = centreon.execute('''echo '{0}' > {1}'''.format(ini, remoteini))
exit_status = stdout.channel.recv_exit_status()
wait.Stop(exit_status)

if not stderr.read():
    wait.Start('Waiting for Centreon API')
    stdin, stdout, stderr = centreon.execute('''export TERM=linux; export PATH=/sbin:/bin:/usr/sbin:/usr/bin
        /path/to/centreon-orchestration/centreon-orchestration.py -i {0} -u {1}'''.format(remoteini, centreon.user))

    sleep(2)
    stdin.write('{0}\n'.format(centreon.password))
    stdin.flush()
    exit_status = stdout.channel.recv_exit_status()
    
    wait.Stop(exit_status, proceed=True)
    output = stdout.read().strip()
    if output:
        print("\033[F{0}\033[K".format(output))
    exit(exit_status)
else:
    print(stderr.read())

centreon.close()