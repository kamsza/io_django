#!/bin/sh

# https://stackoverflow.com/questions/2990414/echo-that-outputs-to-stderr
errcho(){ >&2 echo "$@"; }

# run as root, obviously
if [ `id -u` != 0 ]; then
    errcho "This script needs to be run as root"
    exit 1
fi

# revert what was done in setup.sh
userdel 0tdns

# remove our crontab entry marked with '<AUTO_GENERATED_0TDNS_ENTRY>'
# we also remove the 'DO NOT EDIT' header, as in setup.sh
crontab -l 2> /dev/null |
    grep -vE '^# DO NOT EDIT THIS FILE|^# \(- installed on .*\)|^# \(Cron version .*\)' |
    grep -v '<AUTO_GENERATED_0TDNS_ENTRY>' | crontab

# if told to - also revert what was done in install.sh
if [ "x$1" = "x--delete-files" ]; then
    rm -r /var/lib/0tdns/
    rm -r /etc/netns/0tdns*
    rm /usr/sbin/hourly.py
    rm /usr/sbin/check_if_done.py
    rm -r /etc/0tdns
    rm /usr/lib/python3/dist-packages/ztdnslib.py
fi
