SatellitePackage() {
    rpm -q katello-ca-consumer-$1 > /dev/null
    if [ $? == 1 ]; then
        wget https://$1/pub/katello-ca-consumer-latest.noarch.rpm -O /tmp/katello-ca-consumer-latest.noarch.rpm 2> /dev/null
        yum install /tmp/katello-ca-consumer-latest.noarch.rpm -y > /dev/null
    fi
    Assert "Red Hat Satellite 6 package install"
}

SatelliteRegister() {
    subscription-manager status > /dev/null
    if [ $? == 1 ]; then
        subscription-manager register --org=$1 --activationkey=$2 > /dev/null
    fi
    Assert "Red Hat Satellite 6 register"
}

SSHForward() {
    sshpass -p$4 ssh -o 'ExitOnForwardFailure yes' -oStrictHostKeyChecking=no -oCheckHostIP=no -fN $1@$2 -L $3 2> /dev/null
    return $exitstatus
}

SSHClose() {
    ssh_pids=`ps ax | grep "ssh -o ExitOnForwardFailure yes -oStrictHostKeyChecking=no -oCheckHostIP=no -fN $1@$2 -L $3" | head -1 | xargs | cut -d ' ' -f 1`

    for each in $ssh_pids; do
        kill -1 $each &> /dev/null
    done
}