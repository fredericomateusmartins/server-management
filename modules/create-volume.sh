#!/usr/bin/env bash

# Create and format new volume 

# Library functions import
source $1/library/conditions.sh

# Hard disk drive select
echo "Warning: Total disk size will be used for additional volume creation"
default=`ls -t /dev/sd? | tail -1`
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
fi

# Volume creation with parted
Interactive $3 "Volume is $volume, continue?" ":" "exit"
parted --script -a optimal "$drive" mklabel gpt mkpart /data 0% 100%
if [ $? != 0 ]; then
    false; Assert "Creating volume with Parted"
    exit
else
    true; Assert "Volume creation with Parted"
    partprobe $drive
fi

# Format volume and create filesystem
directory=$(Interactive "string" "Volume mount? [/data]" "echo %s" $4)
if [ -z $directory ]; then
    directory=/data
fi
mkfs.xfs -f -L $directory $volume > /dev/null
Assert "Filesystem creation"

# Fstab volume configuration
mkdir -p $directory
uuid=`blkid $volume | cut -d'"' -f4`
grep $directory /etc/fstab
if [ $? == 1 ]; then
    echo "UUID=$uuid    $directory  xfs defaults    0 0" >> /etc/fstab
    mount -a
fi
Assert "Fstab volume configuration"