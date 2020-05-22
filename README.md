# 0TDNS - Zero Trust DNS
A way to control YOUR name resolution

First - get some openvpn config; http://vpngate.net seems like a good place to go

ACHTUNG! Openvpn configs can be malicious and can execute arbitrary commands on
your system! Always look into the config before using it :)

Now let's say you want to run `ping fsf.org` through openvpn connection.
Let's say `conf.ovpn` is your openvpn config file.
First, prepare your system (account creation and the like):

    # ./install.sh

Now, execute:

    # ./vpn_wrapper.sh conf.ovpn ping devuan.org

Enjoy!

If you don't want to be playing with 0tdns anymore - run:

    # ./uninstall.sh

All the heavy stuff is yet to be added ;)
