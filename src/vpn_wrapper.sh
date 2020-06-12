#!/bin/sh

# We give the full path, because PATH environment variable
# might be unset if run by cron
OVPN_COMMAND="/usr/sbin/openvpn"

OPENVPN_CONFIG="$1"
PHYSICAL_IP="$2"
ROUTE_THROUGH_VETH="$3"
# rest of args is the command to run in network namespace
shift
shift
shift

# for routing some traffic from within the namespace to physical
# network (e.g. database connection) we need to create a veth pair;
# as we want multiple instances of vpn_wrapper.sh to be able to
# run simultaneously, we need unique ip addresses for them;
# the solution is to derive an ip address from current shell's
# PID (which is unique within a system)
NUMBER=$((($$ - 1) * 4))
WORD0HOST0=$(($NUMBER % 256 + 1))
WORD0HOST1=$(($NUMBER % 256 + 2))
NUMBER=$(($NUMBER / 256))
WORD1=$(($NUMBER % 256))
NUMBER=$(($NUMBER / 256))
WORD2=$(($NUMBER % 256))
VETH_HOST0=10.$WORD2.$WORD1.$WORD0HOST0
VETH_HOST1=10.$WORD2.$WORD1.$WORD0HOST1

# to enable multiple instances of this script to run simultaneously,
# we tag namespace name with this shell's PID
NAMESPACE_NAME=0tdns$$
NETNS_SCRIPT=/var/lib/0tdns/netns-script

# in case we want some process in the namespace to be able
# to resolve domain names via libc we put some random public
# dns in namespace sepcific's resolv.conf;
# note, that while libunbound we're using will probably have
# dns addresses provided by us, it is still possible to pass
# a domain name as forwarder address to unbound, in which case
# it will try to resolve it first using libc
DEFAULT_DNS=23.253.163.53
mkdir -p /etc/netns/$NAMESPACE_NAME/
echo nameserver $DEFAULT_DNS > /etc/netns/$NAMESPACE_NAME/resolv.conf

# starts openvpn with our just-created helper script, which calls
# the netns-script, which creates tun inside network namespace
# of name $NAMESPACE_NAME
# we could consider using --daemon option instead of &
$OVPN_COMMAND --ifconfig-noexec --route-noexec --up $NETNS_SCRIPT \
	      --route-up $NETNS_SCRIPT --down $NETNS_SCRIPT \
	      --config "$OPENVPN_CONFIG" --script-security 2 \
	      --connect-timeout 20 \
	      --setenv NAMESPACE_NAME $NAMESPACE_NAME \
	      --setenv WRAPPER_PID $$ \
	      --setenv VETH_HOST0 $VETH_HOST0 \
	      --setenv VETH_HOST1 $VETH_HOST1 \
	      --setenv ROUTE_THROUGH_VETH $ROUTE_THROUGH_VETH\ $DEFAULT_DNS/32 \
	      --setenv PHYSICAL_IP $PHYSICAL_IP &

OPENVPN_PID=$!

# waiting for signal from our netns script
# https://stackoverflow.com/questions/9052847/implementing-infinite-wait-in-shell-scripting
trap true usr1

# wait on openvpn process;
# if we get a signal - wait will terminate;
# if openvpn process dies - wait will also terminate
wait $OPENVPN_PID

# TODO check which of 2 above mention situations occured and
# return from script with error code if openvpn process died

# run the provided command inside newly created namespace
# under '0tdns' user;
sudo ip netns exec $NAMESPACE_NAME sudo -u 0tdns "$@"

# close the connection
kill $OPENVPN_PID
wait $OPENVPN_PID

# we no longer need those
rm -r /etc/netns/$NAMESPACE_NAME/
