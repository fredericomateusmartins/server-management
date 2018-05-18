#!/usr/bin/env bash

# Prepare template for needed modifications and updates

# Library functions import
source $1/library/conditions.sh
source $1/library/operations.sh
source $1/library/services.sh

# Declare associative arrays
declare -A sat

# Array Satellite variables
sat[host]=satellite.example.com
sat[key]=DEFAULT-KEY
sat[org]=TEAM-NAME

# Change interface configurations
cp -f $1/templates/ifcfg-eth0 /etc/sysconfig/network-scripts/ifcfg-eth0
if [ ! -z $2 ] && [ $2 == true ]; then
    Replace "IPADDR" "10.128.122.250" "/etc/sysconfig/network-scripts/ifcfg-eth0"
    Replace "GATEWAY" "10.128.122.1" "/etc/sysconfig/network-scripts/ifcfg-eth0"
fi
nmcli connection reload > /dev/null
InterfaceRestart eth0
Assert "Temporary IP address `grep ^IPADDR= /etc/sysconfig/network-scripts/ifcfg-eth0 | cut -d '=' -f 2` assigned to eth0"

# Install Satellite CA RPM
SatellitePackage ${sat[host]}

# Register Server in Satellite
SatelliteRegister ${sat[org]} ${sat[key]}