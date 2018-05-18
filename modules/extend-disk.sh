#!/usr/bin/env bash

# Extend virtual disk after resize in hypervisor

# Library functions import
source $1/library/conditions.sh

# Hard disk drive select
echo "Warning: Total disk size will be used for extend, please perform a backup prior to operation for it may lead to data loss"
default=`ls -t /dev/sd* | tail -1`
drive=$(Interactive "string" "Hard disk drive device path? [$default]" "echo %s" $2)
if [ -z $drive ]; then
    drive=$default
fi
volume="$drive"1

# Possible exceptions
if  [ ! -e $drive ]; then
    false; Assert "Device $drive does not exist"
    exit
elif [ $drive == "/dev/sda" ]; then
    false; Assert "Device $drive is the OS disk"
    exit
elif grep -qs $drive /proc/mounts; then
	false; Assert "Device $drive is mounted, must be unmounted for extent"
	exit
fi

# Volume creation with parted
Interactive $3 "Volume is $volume, continue?" ":" "exit"
parted --script $drive rm 1
parted --script -a optimal $drive mklabel gpt mkpart /data 0% 100%
if [ $? != 0 ]; then
    false; Assert "Volume creation with Parted"
    exit
fi
Assert "Volume creation with Parted"
partprobe $drive
mount -a