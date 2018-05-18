Assert() {
    if [ $? == 0 ]; then
        echo -e "\e[32mSuccess\e[0m: $1"
    else
        echo -e "\e[31mFailed\e[0m: $1"
        if [ "$2" == true ]; then
            exit 1
        fi
    fi
}

Boolean() {
    read -r -p "$1 [y/N] " answer
    case $answer in
        [yY][eE][sS]|[yY])
            eval $2;;
        *)
            eval $3;;
    esac
}

Choice() {
    read -r -p "$1 " answer
    eval $(printf "${2}" "${answer}")
}


Interactive() {
    if [ ! -z $1 ] && [ $1 == true ]; then
        eval $3
    elif [ ! -z $1 ] && [ $1 == "string" ] && [ $4 != false ]; then
        eval $(printf "${3}" "${4}")
    elif [ ! -z $1 ] && [ $1 == "string" ]; then
        Choice "$2" "$3"
    else
        Boolean "$2" "$3" "$4"
    fi
}