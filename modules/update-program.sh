#!/usr/bin/env bash

# Git local repository update

# Library functions import
source $1/library/conditions.sh
source $1/library/operations.sh
source $1/library/services.sh

# Ask user network password
trap 'echo;stty echo echok;exit' SIGINT
echo -n 'Network password: '
read -s password
echo

# Declare associative arrays
declare -A ssh
declare -A git

# Array SSH variables
ssh[user]=`who am I | awk '{print $1}' | tr -d '\n'`
ssh[proxy]=satellite.example.com
ssh[forward]=10443:github.com:443

# Array Git variables
git[url]=github.com:10443/flippym/server-management.git
git[temp]=/tmp/server-management

if [ $2 == false ]; then
    git[branch]=master
else
    git[branch]=$2
fi

GitUpdate() { # Fetch and merge remote repository to local
    cd $1
    
    if [ -e $PWD/.git ]; then # Checks for local repository
        git remote set-url origin https://${ssh[user]}:$password@${git[url]} &> /dev/null
        git pull &> /dev/null
        git reset --hard origin/${git[branch]} &> /dev/null
    else
        git clone https://${ssh[user]}:$password@${git[url]} ${git[temp]} &> /dev/null
        rsync -avz --delete "${git[temp]}/" "$1/" &> /dev/null; rm -rf ${git[temp]} # Moves cloned repository
    fi
    
    Assert "Update Git local repository"
    
    chmod +x server-management.py modules/*
    ln -sf $1/server-management.py /usr/local/sbin/server-management
}

# Check if SSH port is open
Connect ${ssh[proxy]} 22
Assert "SSH port accessible"

if [ ! `Connect ${ssh[proxy]} 22; echo $?` -eq 0 ]; then
    wget -r -np -nH –cut-dirs=3 -R index.html* https://satellite.example.com/pub/server-management/ -P /tmp &> /dev/null
    rsync -avz --delete "/tmp/pub/server-management/" "$1/" --exclude 'git.log' &> /dev/null; rm -rf /tmp/pub
    chmod +x $1/server-management.py $1/modules/* &> /dev/null
    ln -sf $1/server-management.py /usr/local/sbin/server-management &> /dev/null
    Assert "Update Git local repository through Satellite"
    exit 0
fi

# Trap for keyboard interrupt
trap 'SSHClose $1 $2 $3;exit' SIGINT

SSHForward ${ssh[user]} ${ssh[proxy]} ${ssh[forward]} $password
Assert "SSH port forward" true

GitUpdate $1

SSHClose ${ssh[user]} ${ssh[proxy]} ${ssh[forward]}