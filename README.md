# Server Management <img src="others/icon.png" align="right" width="256" height="256"/>
The `server-management` is intended to be used as a standardized module parser, for easability in adding new code and standardization.
<br>
<br>
The parser will look for modules in the absolute main script directory `modules` and parse them as positional arguments, where `-` will serve as the default splitting character. If there's a file named `first-second.ext`, where `ext` can be any kind of extension, that same module can be executed as:

```shell
server-management first second
```

The parser is also intended to be used to automate practices, meaning there can be given optional arguments for each module in order to prevent interactive sessions.

```shell
server-management first second --boolean --output log
```

The parser looks for a file named `server-management.ini` in the main directory, in order to construct the optional arguments for each module.<br>
For example, the `first-second.ext` module will look for further arguments in the `.ini` file.<br>
_The arguments are parsed by order, meaning the first argument read will be the first argument passed to the module._

```shell
[first-second]
flag:   -b
        -o
name:   --boolean
        --output
action: bool
        str
metavar:-
        var
help:   Sends a 'true' value to the executed module
        Sends the string after the optional argument 
```

<a name="description"></a>Each module description is fetched from the module third line in case that same line is commented. For instance, if there is a comment in `first-second.ext`:

```bash
#!/usr/bin/env bash

# This is a description for parser

...
Code goes in here
...
```

When the parser is executed with an **help** argument it will output the following:

```shell
[root@localhost ~]# server-management first -h
usage: server-management first [-h] <subcommand> ...

Positional:
  <subcommand>
    second       This is a description for parser

Optional:
  -h, --help    Show this help message
```

The parser also has an automatic bash completion mechanism, based on the filenames split format.

```shell
[root@localhost ~]# server-management <tab><tab>
first
[root@localhost ~]# server-management first <tab><tab>
second
```

To use the bash completion mechanism, the files in the regular directory need to be sourced. Append the following `for` loop in `~/.bashrc` to automatically source the files at each session login.

```shell
for file in /etc/bash_completion.d/* ; do
    source "$file"
done
```

The module parser file `server-management.py` will look for missing libraries in the operative system and install them in case they are not installed. To use this feature, simply add a new package to the list in the file, such as `test-library`.

```python
#!/usr/bin/env python

# Needed Python libraries from library
import Package
Package(['python-configparser', 'python2-paramiko', 'test-library'])
...
```

# Real-Life Usages
Use `server-management -h` or `--help`, for possible input arguments and each positional arguments description if properly [configured](#description) in each module.

```shell
[root@localhost ~]# server-management --help
usage: server-management [-h] [-v] <command> ...

RHEL7 Server Management
-----------------------
   RHEL Server
   Management Tools

Positional:
  <command>      To see available options, use --help with each command
    clone
    configure
    extend
    update
    create
    template

Optional:
  -h, --help     Show this help message
  -v, --version  Show program version

Check the git repository at https://github.com/flippym/server-management/,
for more information about usage, documentation and bug report.
```

Edit virtual machine network configurations and disk provisioning automation on **clean deploy**.

```shell
server-management configure server --gateway 10.2.38.1
```

Register virtual machine in Red Hat Satellite 6 on **clean deploy** or **template edit** in order to install RHEL packages.

```shell
server-management configure satellite --simple-registration
```

List available activation keys in Red Hat Satellite 6 on **clean deploy** in order to register with a given key.

```shell
server-management configure satellite --list-keys
```

Create product, repository and activation key automatically in Satellite, in order to use custom repositories for that cluster and register virtual machine on **clean deploy**. <br>
_If an activation key is already created for that cluster name, the machine will be automatically registered in that same activation key._

```shell
server-management configure satellite --cluster-name example --force
```

Configure alarms and monitoring for virtual machine on **clean deploy**.

```shell
server-management configure centreon --user ldapuser
```

Create and format a new volume using all given disk space on **clean deploy**.
If the `--drive`, followed by a drive file path, argument is not given, it will be prompt at the module begin.
If the `--mount`, followed by a inexistent directory path, argument is not given, it will be prompt at the module begin.
If the `--force` argument is not given, a yes or no will be prompt.

```shell
server-management create volume --drive /dev/sdb --mount /newdir --force
```

Create and format a new volume group using all given disk space on **clean deploy**.
If the `--drive`, followed by a drive file path separated by commas, argument is not given, it will be prompt at the module begin.
If the `--mount`, followed by a inexistent directory path, argument is not given, it will be prompt at the module begin.
If the `--force` argument is not given, a yes or no will be prompt.
If the `--label` argument is not given, it will be prompt at the module begin.

```shell
server-management create group --drive /dev/sdb,/dev/sdc,/dev/sdd,/dev/sde --force --mount /data --label test
```

Extend virtual disk after resize in hypervisor on **clean deploy**.
If the `--drive`, followed by a drive file path, argument is not given, it will be prompt at the module begin.
If the `--force` argument is not given, a yes or no will be prompt. <br>
_In case the install is not fresh and there's data in the drive, backup the data or snapshot the machine for there may be data loss._

```shell
server-management extend disk --drive /dev/sdb --force
```

Update local git repository to fetch the latest version.

```shell
server-management update program --branch master
```

Update bash completion file in `/etc/bash_completion.d/` based on current files in the modules directory. <br>
_Logout and login again for changes to take effect_.

```shell
server-management update bash
```

Clean virtual machine clutter and prepares it for template conversion on **template edit**.
If the `--poweroff` argument is not given, it will be prompt at the module end.

```shell
server-management template clean --poweroff
```