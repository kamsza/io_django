#!/bin/sh

# run this script as root

# more could go here (e.g. initialization of postgres database)

mkdir -p /var/lib/0tdns/

mkdir -p /etc/netns/0tdns/

# in case we want some process in the namespace to be able
# to resolve domain names via libc we put some random public
# dns in namespace sepcific's resolv.conf;
# note, that while libunbound we're using will probably have
# dns addresses provided by us, it is still possible to pass
# a domain name as forwarder address to unbound, in which case
# it will try to resolve it first using libc
echo nameserver 23.253.163.53 > /etc/netns/0tdns/resolv.conf

# part of the program running inside network namespace
# will run under this user
sudo useradd --system 0tdns
