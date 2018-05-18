#!/usr/bin/env python

# Bash completion modules update

from ast import literal_eval
from sys import argv
from textwrap import dedent


class Completion(object):

    array = literal_eval(argv[2])
    progname = 'server-management'
    subparsers = set()

    def __init__(self):
    
        self.Update()


    def Update(self):
    
        for name in self.array.keys(): # Dynamic bash completion subparser syntax
            variables = ' '.join(self.array[name])
            self.subparsers.add('{0}="{1}"'.format(name, variables))
    
        with open("/etc/bash_completion.d/{0}".format(self.progname), "w") as openbash:
            openbash.write(dedent("""\
                _{0}()
                {{
                    local cur prev opts
                    COMPREPLY=()
                    cur="${{COMP_WORDS[COMP_CWORD]}}"
                    prev="${{COMP_WORDS[COMP_CWORD-1]}}"
                    serv="{1}"
                    {2}
                    opts="--help --version"
                    if [[ ${{cur}} == -* ]] ; then
                        COMPREPLY=( $(compgen -W "${{opts}}" -- ${{cur}}) )
                        return 0
                    elif [[ $prev == {0} ]] ; then
                        COMPREPLY=( $(compgen -W "${{serv}}" -- ${{cur}}) )
                        return 0
                    else
                        for each in $serv ; do
                            if [[ ${{prev}} == $each ]] ; then
                                COMPREPLY=( $(compgen -W "${{!each}}" -- ${{cur}}) )
                                return 0
                            fi
                        done
                    fi
                }}
                complete -F _{0} {0}""").format(self.progname, ' '.join(self.array.keys()), '\n    '.join(self.subparsers)))


try:
    Completion()
    status = '\033[32mSuccess\033[0m'

except:
    status = '\033[31mFailed\033[0m'
    
print("{0}: Bash completion update".format(status))