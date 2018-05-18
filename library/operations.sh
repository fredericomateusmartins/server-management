ByteConversion() {
    printf "%.0f\n" $(($1/1024/1024**2))
}

Connect() {
    nc -w 1 $1 $2 < /dev/null &> /dev/null
}

DiskProbe() {
    ls /sys/class/scsi_host/ | while read host; do 
        echo "- - -" > /sys/class/scsi_host/$host/scan
    done
}

Graceful() {
    for each in `ls /etc/sysconfig/network-scripts/ifcfg-eth*`; do
        sed -i '/^GATEWAY=/d' $each
        sed -i '/^DNS.*=/d' $each
        sed -i '/^DOMAIN=/d' $each
        sed -i '/^check_link_down/,$d' $each
        InterfaceRestart `echo $each | cut -d '-' -f 3`
    done
}

Hostname() {
    hostnamectl status | grep 'Static hostname:' | cut -d ':' -f 2 | xargs
}

InterfaceRestart() {
    nmcli connection down $1 > /dev/null
    nmcli connection up $1 > /dev/null
}

Replace() {
    sed -i "s/\(^$1 *= *\).*/\1$2/" $3
}

Shutdown() {  # Shutdown and kicks user out of shell
    shutdown -t 5 --no-wall &> /dev/null
    for process in $(fuser /dev/pts/$(who am I | cut -d ' ' -f 2 | cut -d '/' -f 2) 2> /dev/null); do
        kill -9 $process
    done
}