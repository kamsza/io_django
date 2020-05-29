#!/bin/sh

OPENVPN_CONFIG="$1"
# rest of args is the command to run in network namespace
shift

# just in case something causes more instances of this script
# to run simultaneously, we timestamp some names
SECONDS=`date '+%s'`

HELPER_SCRIPT=/var/lib/0tdns/helper_script$SECONDS.sh
NAMESPACE_NAME=0tdns$SECONDS

# we create another script as a way of passing variables
# to netns-script
cat > $HELPER_SCRIPT <<EOF
#!/bin/sh

export NAMESPACE_NAME=$NAMESPACE_NAME
export WRAPPER_PID=$$

/var/lib/0tdns/netns-script "\$@"
EOF

chmod u+x $HELPER_SCRIPT

# in case we want some process in the namespace to be able
# to resolve domain names via libc we put some random public
# dns in namespace sepcific's resolv.conf;
# note, that while libunbound we're using will probably have
# dns addresses provided by us, it is still possible to pass
# a domain name as forwarder address to unbound, in which case
# it will try to resolve it first using libc
mkdir -p /etc/netns/$NAMESPACE_NAME/
echo nameserver 23.253.163.53 > /etc/netns/$NAMESPACE_NAME/resolv.conf

# starts openvpn with our just-created helper script, which calls
# the netns-script, which creates tun inside network namespace
# of name $NAMESPACE_NAME
# we could consider using --daemon option instead of &
openvpn --ifconfig-noexec --route-noexec --up $HELPER_SCRIPT \
	--route-up $HELPER_SCRIPT --down $HELPER_SCRIPT \
	--config "$OPENVPN_CONFIG" --script-security 2 &

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
rm -r $HELPER_SCRIPT /etc/netns/$NAMESPACE_NAME/
