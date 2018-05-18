#!/usr/bin/env bash

# Virtual machine system configuration 

# Library functions import
source $1/library/conditions.sh
source $1/library/operations.sh

# Declare associative arrays
declare -A oem

# Array OEM variables
oem[ip]=`ip addr show eth0 | awk '/inet/ { print $2 }' | cut -d '/' -f 1`
if [ -z ${oem[ip]} ]; then
    false; Assert "Interface eth0 must be active"
    exit 1
fi
default=$(echo ${oem[ip]} | cut -d . -f 1-3).1
oem[gateway]=$(Interactive "string" "Interface eth0 gateway? [$default]" "echo %s" $2)
if [ -z ${oem[gateway]} ]; then
    oem[gateway]=$default
fi
if [ -z ${oem[ip]} ] || [ -z ${oem[gateway]} ]; then
    false; Assert "Fetching IP or Gateway from interface"
    exit 1
fi

# Remove default gateway from eth0
nmcli connection modify eth0 ipv4.never-default yes
Assert "Default eth0 gateway removal"

# Hosts file restore and IP/Hostname assertion
cp -f $1/templates/hosts /etc/hosts
sed -i -ce s/SRVNAME/$(Hostname)/g /etc/hosts
sed -i -ce s/IPOEM/${oem[ip]}/g /etc/hosts
Assert "Hosts file assertion"

# NTP server configuration
cp -f $1/templates/ntp.conf /etc/ntp.conf
echo "server ${oem[gateway]}" >> /etc/ntp.conf
Assert "NTP server configuration"

# Configure Secure Firewall
firewall-cmd --set-default-zone=external &> /dev/null
firewall-cmd --zone=external --change-interface=eth1 &> /dev/null
firewall-cmd --zone=internal --change-interface=eth0 &> /dev/null
Assert "Firewall secure configuration"

# Configure network routes
cp -f $1/templates/route-eth0 /etc/sysconfig/network-scripts/route-eth0
sed -i -ce s/GWOEM/${oem[gateway]}/g /etc/sysconfig/network-scripts/route-eth0
Assert "Network routes assertion"

# Domain names resolution configuration
cp -f $1/templates/resolv.conf /etc/resolv.conf
Assert "Name resolution restore"

# Update known certificates
for each in `ls $1/templates/*.pem`; do
    openssl x509 -in $each -noout
    if [ $? -eq 0 ]; then
        cp $each /etc/pki/ca-trust/source/anchors/
    fi
done
update-ca-trust

# Remove all clutter inserted by vCenter in the network interface configurations
# Graceful
# Assert "Network interface cleaning"

systemctl restart network
Assert "Network interface configurations restart"