#!/bin/sh

# run as root, obviously

# revert what was done in setup.sh
userdel 0tdns

# if told to - also revert what was done in install.sh
if [ "x$1" = "x--delete-files" ]; then
    rm -r /var/lib/0tdns/
    rm -r /etc/netns/0tdns*
    rm /usr/sbin/hourly.sh /usr/sbin/hourly.py
fi
