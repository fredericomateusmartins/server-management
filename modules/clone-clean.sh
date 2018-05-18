#!/usr/bin/env bash

# Prepare virtual machine after cloning 

# Library functions import
source $1/library/conditions.sh

# Clean logs and journal
journalctl --vacuum-time=0 2> /dev/null
for l in secure cron dmesg messages secure wtmp audit/audit.log messages boot.log; do
  cat /dev/null > /var/log/$l
done
Assert "Log and journal clear"

# Clean configurations
rm -f /etc/ssh/ssh_host_*
rm -f /etc/udev/rules.d/70-persistent-net.rules
Assert "SSH keys and MAC address removal"

# Clear history
cat /dev/null > /root/.bash_history
Assert "Bash history clean"

# Clean tmp
rm -rf /tmp/*
Assert "Temporary directory clean"

# Remove RHSAT Registration
subscription-manager status > /dev/null
if [ $? == 0 ]; then
    subscription-manager remove --all > /dev/null
    subscription-manager unregister > /dev/null
    subscription-manager clean > /dev/null
fi
Assert "Red Hat Satellite 6 registration removal"

# Uninstall Satellite package
rpm -q katello-ca-consumer-rhsat.srv.vodafone.pt > /dev/null
if [ $? == 0 ]; then
    rpm -e katello-ca-consumer-rhsat.srv.vodafone.pt > /dev/null
fi
Assert "Red Hat Satellite 6 RPM uninstall"

# Remove Home Directories
for each in `ls /home/`; do
    if [ $each != admin ]; then
        rm -rf /home/$each
    fi
done
Assert "Home directories removal"

echo "\
ATENÇÃO: Mudar hostname da máquina    
         IP das interfaces
         Registar máquina no Satellite"