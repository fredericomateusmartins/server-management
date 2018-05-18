#!/usr/bin/env bash

# Prepare template for virtual machine deployment 

# Library functions import
source $1/library/conditions.sh
source $1/library/operations.sh

# Check before delete
Interactive $3 "This operation will clear any configurations made. Proceed?" ":" "exit"

# Clean logs and journal
journalctl --vacuum-time=0 2> /dev/null
for l in secure cron dmesg messages secure wtmp audit/audit.log messages boot.log; do
  cat /dev/null > /var/log/$l
done
Assert "Log and journal clear"

# Clean configurations
rm -f /etc/ssh/ssh_host_*
rm -f /etc/udev/rules.d/70-persistent-net.rules
rm -f /etc/sysconfig/network-scripts/route-eth*
nmcli connection reload
Assert "SSH keys and network rules removal"

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

# Rename hostname
hostnamectl set-hostname newvirtualmachine
Assert "Hostname reset"

# Remove Home Directories
for each in `ls /home/`; do
    if [ $each != admin ]; then
        rm -rf /home/$each
    fi
done
Assert "Home directories removal"

Interactive $2 "Shutdown virtual machine?" "Shutdown" "exit"