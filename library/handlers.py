import sys

from functools import partial
from Queue import Empty, Queue
from os import devnull, system
from signal import SIGINT, signal
from socket import gethostname, socket
from subprocess import PIPE, Popen
from threading import Thread
from time import sleep
from traceback import format_tb
from yum import Errors, YumBase


def Boolean(argument, question):

    if argument == 'true':
        answer = 'yes'
    else:
        answer = raw_input("{} [y/N] ".format(question))
    if answer.lower() == 'y' or answer.lower() == 'ye' or answer.lower() == 'yes':
        return True

    return False


def Interactive(argument, question, default):

    if argument == 'false':
        try:
            answer = raw_input("{} [{}] ".format(question, default))
        except KeyboardInterrupt:
            exit()
        if not answer:
            answer = default
    else:
        answer = argument

    return answer


def GetUser(user=None):

    sysuser, status = Popen("who am I | awk '{print $1}' | tr -d '\n'", shell=True, stdout=PIPE, stderr=PIPE).communicate()
    
    if user == 'false':
        user = sysuser

    while user == 'root':
        print("Warning: LDAP username can't be root")
        user = raw_input("Username: ")

    return user


def GetSystemVersion():
    
    release = Popen("uname -r", shell=True, stdout=PIPE, stderr=PIPE).communicate()[0]
    major = release.split('.')[-2][-1]
    
    return int(major)


class OutputWaiting(object):

    pipe = Queue()

    def __init__(self, function=None):

        sys.excepthook = self.Exception
        signal(SIGINT, self.Interrupt)

        self._function = function

    def __call__(self, string, force, *args, **kwargs):

        self.Start(string)
        
        if hasattr(self, '_instance'):
            exit_status = self._function(self._instance, *args, **kwargs)
        else:
            exit_status = self._function(*args, **kwargs)
            
        self.Stop(exit_status, force)
        return exit_status
        
    def __get__(self, instance, owner):
        
        self._instance = instance
        return partial(self.__call__)

    def Start(self, string):

        self.string = string
        self.animation = Thread(target=self.Execute)
        self.animation.daemon = True

        self.animation.start()
        system('setterm -cursor off')

    def Stop(self, error=None, proceed=False):

        if error:
            self.pipe.put('error', block=True)
        else:
            self.pipe.put(True, block=True)

        try:
            self.animation.join()
        except AttributeError:
            print

        system('setterm -cursor on')

        if error and not proceed:
            exit(-1)

    def Execute(self):

        data = False

        while not data:
            for char in ['|', '/', '-', '\\']:
                print '', char, ':', self.string, '\033[F'
                sleep(0.12)

                try:
                   data = self.pipe.get(data)
                except Empty:
                    pass

                if data == 'error':
                    self.Error(self.string)
                    break
                elif data:
                    self.Success(self.string)
                    break

    def Exception(self, error, value, trace):

        print('\033[KTraceback (most recent call last):\n{1}{0}: {2}'.format(error.__name__, ''.join(format_tb(trace)), value))
        self.Stop(error=True)

    def Interrupt(self, signal, frame):

        sys.stdout.write('\b\b\r')
        sys.stdout.flush()
        self.Stop(error=True)
    
    @staticmethod
    def Error(string):

        print("\033[31mFailed\033[0m: {0}\033[K".format(string))
    
    @staticmethod
    def Success(string):

        print("\033[32mSuccess\033[0m: {0}\033[K".format(string))
    
    @staticmethod
    def Warning(string):

        print("\033[33mWarning\033[0m: {0}\033[K".format(string))
    
    @staticmethod
    def Info(string):

        print("\033[36mInfo\033[0m: {0}\033[K".format(string))


class Monitor(object):

    def __init__(self, host, hostname):

        self.host = host
        self.hostname = hostname

    @OutputWaiting
    def Host(self):

        return system('ping -c 1 -W 1 {} &> /dev/null'.format(self.host))

    @OutputWaiting
    def Katello(self):

        if system('rpm -q katello-ca-consumer-{} > /dev/null'.format(self.host)):
            system('rpm -i https://{}/pub/katello-ca-consumer-latest.noarch.rpm > /dev/null'.format(self.host))

        with open('/etc/rhsm/facts/katello.facts', 'w') as openfacts:
            openfacts.write('{{"network.hostname-override":"{0}"}}'.format(self.hostname))

        return system('rpm -q katello-ca-consumer-{} > /dev/null'.format(self.host))

    @OutputWaiting
    def Port(self, port):

        s = socket()
        s.settimeout(1)
        
        return s.connect_ex((self.host, port))
        

class Package(object):
    
    def __init__(self, packages):
        
        if type(packages) is list or type(packages) is tuple or type(packages) is set:
            pass
        elif type(packages) is str:
            packages = [packages]
        else:
            OutputWaiting.Info('Packages to be asserted must be in string or list format')
            exit(-1)
        
        for package in packages:
            if self.Check(package):
                self.Install('Installing package {}'.format(package), True, package)
    
    def Check(self, package):
        
        return system('rpm -q {} > /dev/null'.format(package))
        
    @OutputWaiting
    def Install(self, package):
    
        return system('yum -y install {} > /dev/null'.format(package))