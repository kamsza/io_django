#!/bin/sh

# We give the full path, because PATH environment variable
# might be unset if run by cron
OVPN_COMMAND="/usr/sbin/openvpn"

OPENVPN_CONFIG="$1"
# for routing some traffic from within the namespace to physical
# network (e.g. database connection) we need to create a veth pair;
# ip datagrams routed through veth pair are going to have veth's private address
# as their source address - we need to change it to the address of our physical
# network device using iptables' SNAT. This address is provided by the caller.
PHYSICAL_IP="$2"
# as we want multiple instances of vpn_wrapper.sh to be able to
# run simultaneously, we need unique ip addresses for veth devices, which
# caller provides to us in command line arguments
VETH_HOST0="$3"
VETH_HOST1="$4"
# caller specifies space-delimited subnets, traffic to which should not be
# routed through the vpn (<database_ip>/32 is going to be here)
ROUTE_THROUGH_VETH="$5"
# we use a unique id provided in 6th argument to tag namespace name
ID="$6"

# rest of args is the command to run in network namespace
for _ in `seq 6`; do
    shift
done

# to enable multiple instances of this script to run simultaneously,
# we tag namespace name
NAMESPACE_NAME=0tdns$ID
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
	      --connect-timeout 20 --connect-retry-max 1 --verb 0 \
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
# if we get sigusr1 from netns-script - wait will
# terminate with 138 (128 + signal number);
# if openvpn process dies - wait will also terminate,
# but with openvpn's exit value
wait $OPENVPN_PID

if [ $? = 138 ]; then
    # we received sigusr1 from netns-script, namespace is ready

    # run the provided command inside newly created namespace
    # under '0tdns' user;
    sudo ip netns exec $NAMESPACE_NAME sudo -u 0tdns "$@"

    if [ $? = 0 ]; then
	RETVAL=0
    else
	RETVAL=2
    fi
    
    # close the connection
    kill $OPENVPN_PID
    wait $OPENVPN_PID
else
    RETVAL=1
fi

# we no longer need those
rm -r /etc/netns/$NAMESPACE_NAME/

# return 0 on success, 1 on failed vpn connection,
# 2 on problems within the program we ran in the namespace
exit $RETVAL
