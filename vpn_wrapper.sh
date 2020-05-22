#!/bin/sh

OPENVPN_CONFIG="$1"
# rest of args is the command to run in network namespace
shift

echo -n $$ > /var/lib/0tdns/shell_pid

# starts openvpn with the netns-script,
# that creates tun inside network namespace 0tdns;
# we could consider using --daemon option instead of &
openvpn --ifconfig-noexec --route-noexec --up netns-script \
	--route-up netns-script --down netns-script \
	--config "$OPENVPN_CONFIG" --script-security 2 &

OPENVPN_PID=$!

# waitin for signal from our netns script
# https://stackoverflow.com/questions/9052847/implementing-infinite-wait-in-shell-scripting
trap true usr1

# wait on openvpn process;
# if we get a signal - wait will terminate;
# if openvpn process dies - wait will also terminate
wait $OPENVPN_PID

# TODO check which of 2 above mention situations occured and
# return from script with error code if openvpn process died

# we no longer need this file
rm /var/lib/0tdns/shell_pid
    
# run the provided command inside '0tdns' namespace
# under '0tdns' user;
sudo ip netns exec 0tdns sudo -u 0tdns "$@"

# close the connection
kill $OPENVPN_PID
wait $OPENVPN_PID
