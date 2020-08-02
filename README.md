# 0TDNS - Zero Trust DNS
A way to control name resolution

First - get some openvpn config; http://vpngate.net seems like a good place to go

ACHTUNG! Openvpn configs can be malicious and can execute arbitrary commands on
your system! Always look into the config before using it :)

Now let's say you want to run `ping fsf.org` through openvpn connection.
Let's say `conf.ovpn` is your openvpn config file.
First, install relevant scripts on your system

    # ./install.sh

You can also install to an arbitrary directory
(0tdns won't run from there, however; this is just to make things easier for
distro packagers or to install in a chroot)

    # ./install.sh /path/to/installation/root

The `install.sh` script above only copies some files to the filesystem.
You also need some setup, which is done with

    # ./setup.sh

For now, the `setup.sh` script creates a `0tdns` user in the system
and adds an entry in root's crontab. Some other setup-related stuff
might be added to it later.

One might wonder why there isn't a single script to install files and
setup the system? The reason is, again, to make things easier for distros.
Packager would install software to a directory and make a package from it
(using appropriate tools, of course). They would use commands from
`setup.sh` to create a script, that is attached to the package and run
at installation.

Now, execute:

    # ./vpn_wrapper.sh conf.ovpn ping fsf.org

the wrapper shall create an openvpn connection and a network namespace with
all packets (except those to localhost) routed through the vpn. It then executes
given command inside the namespace.

For now - this is all that can be simply tried out. Other parts of the project
work with database.

For other half (database creation and front-end) check https://github.com/kamsza/io_django

You can remove te user nad crontab entry with

    # ./uninstall.sh

To do this and also remove files, run

    # ./uninstall.sh --delete-files
