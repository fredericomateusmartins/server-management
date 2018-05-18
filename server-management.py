#!/usr/bin/env python

__version__ = 1

# Needed Python libraries
from library import Package
Package(['python-configparser', 'python2-paramiko', 'python-requests', 'sshpass'])

from argparse import ArgumentError, ArgumentParser, SUPPRESS, RawDescriptionHelpFormatter
from collections import OrderedDict
from configparser import ConfigParser, DuplicateSectionError
from functools import partial
from json import dumps
from linecache import getline
from os import listdir, path, system
from sys import argv
from textwrap import dedent


class Parser(object):

    program = __file__.rpartition('.')[0]

    def __init__(self):

        self.array = Generator().array

        self.Create()
        self.Positional(self.subparser)
        self.Optional(self.parser, True)
        self.Empty()        

        self.parser.parse_args().func() # Parses the arguments to execute a module file


    def Create(self): # Argument parsing structure creation

        self.parser = ArgumentParser(prog=self.program, add_help=False, formatter_class=RawDescriptionHelpFormatter,
                                description=dedent('''\
                                    RHEL7 Server Management
                                    -----------------------
                                       RHEL Server 
                                       Management Tools
                                    '''), epilog=dedent('''\
                                    Check the git repository at https://github.com/flippym/server-management/,
                                    for more information about usage, documentation and bug report.'''))

        self.subparser = self.parser.add_subparsers(title='Positional', help='To see available options, use --help with each command', 
            metavar='<command>')


    def Empty(self):

        if not argv[1:]:
            self.parser.parse_args()
            self.parser.print_help()
            raise SystemExit


    def Positional(self, parser): # Positional arguments creation

        for arg, subarg in self.array.items(): 
            newparser = parser.add_parser(arg, help='', add_help=False)
            subparser = newparser.add_subparsers(title='Positional', metavar='<subcommand>')
            subparser.required = True

            self.Optional(newparser)

            for values in sorted(subarg): # Positional subarguments creation
                positional = subparser.add_parser(values, help=subarg[values][1], add_help=False)
                conditional = self.Conditional(positional, '-'.join([arg, values]))
                positional.set_defaults(func=partial(system, '{0} {1}'.format(subarg[values][0], conditional)))

    def Optional(self, parser, main=False): # Optional arguments creation

        optional = parser.add_argument_group('Optional')
        optional.add_argument('-h', '--help', action='help', help='Show this help message')

        if main:
            optional.add_argument('-v', '--version', action='version', version='{0} {1}'.format(self.program, __version__), 
                help='Show program version')


    def Conditional(self, parser, module): # Reads optional arguments out of ini configuration file

        conditions = [Path.main]
        optional = parser.add_argument_group('Optional')

        try:
            conditions.extend(Structurer(optional, module, self.array).args)
            optional.add_argument('-h', '--help', action='help', help='Show this help message')

        except KeyError:
            pass

        except ArgumentError as error:
            flag = str(error).split(' ')[1].strip(':')
            print("Skipping module file {0}, due to conflict in flags {1}".format(module, flag))

        return ' '.join(conditions)


class Generator(object): # Create a loop to iterate over hyphens to parse each argument

    array = OrderedDict()
    
    def __init__(self):
        
        self.Empty()

        for self.module in listdir(Path.modules):
            if self.Exception():
                continue

            try:
                self.Attribute()
                self.Limiter()
                self.Associate()

            except IndexError:
                self.Notifier("Skipping module file {0}, due to syntax error".format(self.module))
        
    
    def Associate(self):

        try:
            self.array[self.command[0]]

        except KeyError:
            self.array[self.command[0]] = OrderedDict()

        for each in self.command:
            self.array[self.command[0]][self.command[1]] = [path.join(Path.modules, self.module), self.description]


    def Attribute(self):

        comment = getline(path.join(Path.modules, self.module), 3) # Look for description in modules third line

        self.command = self.module.split('.')[0].split('-') # Removes the file extension for parsing arguments
        self.description = comment[1:].strip() if comment.startswith('#') else 'No comment in module {0} first line'.format(self.module)


    def Empty(self): # Check if modules directory is empty

        if not listdir(Path.modules):
            self.Notifier("No files in modules directory")   


    def Exception(self): # Ignore hidden files and directories

        if self.module.startswith('.') or path.isdir(path.join(Path.modules, self.module)):
            return True


    def Limiter(self): # Two arguments limiter

        if not len(self.command) == 2:
            raise IndexError


    def Notifier(self, string):

        print("Warning: {0}".format(string))


class Structurer(object): # Object for handling new actions in optional configurations

    config = ConfigParser()

    def __init__(self, parser, module, array):

        self.array = array
        self.args = list()
        self.module = module
        self.parser = parser
        
        try:
            self.config.read(Path.config)
            
        except DuplicateSectionError as error:
            print("Error: Duplicated entrance {0} in configuration file".format(str(error).split('\'')[3]))
            raise SystemExit
            
        self.Construct(OrderedDict())


    def Construct(self, parameters):

        for param in ['flag', 'name', 'action', 'metavar', 'help']:
            parameters[param] = self.config[self.module][param].splitlines()

        for count in range(len(parameters['name'])):
            if parameters['action'][count] == 'bool':
                self.parser.add_argument(parameters['flag'][count], parameters['name'][count], action='store_true', 
                    help=parameters['help'][count])

                if parameters['name'][count] in argv[3:] or parameters['flag'][count] in argv[3:]:
                    self.args.append('true')

                else:
                    self.args.append('false')

            elif parameters['action'][count] == 'str':
                self.parser.add_argument(parameters['flag'][count], parameters['name'][count], metavar=parameters['metavar'][count],
                    type=str, help=parameters['help'][count])

                if parameters['name'][count] in argv[3:] or parameters['flag'][count] in argv[3:]:
                    for each in [parameters['name'][count], parameters['flag'][count]]:
                        try:
                            self.args.append(argv[3:][argv[3:].index(each)+1])

                        except ValueError:
                            pass
                        except IndexError:
                            pass
                else:
                    self.args.append('false')

            elif parameters['action'][count] == 'completion':
                self.args.append("\'{0}\'".format(dumps(self.array, ensure_ascii=False))) # Escape quotes for argument passing
                

class Path(object):

    main = path.dirname(path.realpath(__file__))
    config = path.join(main, 'server-management.ini')
    modules = path.join(main, 'modules')


Parser()