#!/bin/sh

# revert what was done in install.sh
rm -rf /var/lib/0tdns/

rm -rf /etc/netns/0tdns/

userdel 0tdns
