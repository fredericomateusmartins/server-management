#!/usr/bin/env bash

# Create and format new volume group

# Library functions import
source $1/library/conditions.sh
source $1/library/operations.sh

# Hard disk drive select
DiskProbe
echo "Warning: Total disks size will be used for additional volume creation"
default=`ls -mt /dev/sd? | grep -v /dev/sda | tr -d ' '`
drive=$(Interactive "string" "Hard disk drive devices path? [$default]" "echo %s" $2)
if [ -z $drive ]; then
    drive=$default
fi
directory=$(Interactive "string" "Volume mount? [/data]" "echo %s" $4)
if [ -z $directory ]; then
    directory=/data
fi
label=$(Interactive "string" "Volume group label? [data]" "echo %s" $5)
if [ -z $label ]; then
    label=data
fi

# Possible exceptions
if [ `vgs $label &> /dev/null; echo $?` == 0 ]; then
    false; Assert "Volume group $label already exists, please remove it or choose another label"
    exit
fi
for each in $(echo $drive | sed "s/,/ /g"); do
    if  [ ! -e $each ]; then
        false; Assert "Device $each does not exist"
        exit
    elif [ $each == "/dev/sda" ]; then
        false; Assert "Device $each is the OS disk"
        exit
    elif [ `ByteConversion $(blockdev --getsize64 $each)` -ge 510 ]; then
        false; Assert "Device $each is $(ByteConversion $(blockdev --getsize64 $each))GB, maximum allowed size per disk is 500GB"
        exit
    fi
done

# Volume creation with parted
for each in $(echo $drive | sed "s/,/ /g"); do
    volume="$each"1
    Interactive $3 "Volume is $volume, continue?" ":" "exit"
    parted --script -a optimal "$each" mklabel gpt mkpart "$directory" ext4 0% 100% set 1 lvm on
    if [ $? != 0 ]; then
        false; Assert "Creating volume $each with Parted"
        exit
    else
        true; Assert "Creating volume $each with Parted"
        partprobe $each
    fi
    pvcreate $volume &> /dev/null
    vgs $label &> /dev/null
    if [ $? == 0 ]; then
        vgextend $label $volume &> /dev/null
    else
        vgcreate $label $volume &> /dev/null
    fi
done

# Format volume and create filesystem
if [ $3 == true ]; then
    lvcreate -n $label -l +100%FREE $label --yes &> /dev/null
    mkfs.ext4 /dev/$label/$label -F &> /dev/null
else
    lvcreate -n $label -l +100%FREE $label > /dev/null
    mkfs.ext4 /dev/$label/$label > /dev/null
fi
Assert "Filesystem creation"

# Fstab volume configuration
mkdir -p $directory
uuid=`blkid /dev/mapper/$label-$label | cut -d'"' -f2`
grep $directory /etc/fstab > /dev/null
if [ $? == 1 ]; then
    echo "UUID=$uuid    $directory  ext4 defaults    0 0" >> /etc/fstab
    mount -a
fi
Assert "Fstab volume configuration"