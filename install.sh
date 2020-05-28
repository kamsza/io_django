#!/bin/sh

# If we have an argument - use it as installation root
# and prefer it over INSTALL_ROOT variable;
# Otherwise, use INSTALL_ROOT if set;
# Otherwise, use "/"
if [ "x" != "x$1" ]; then
    INSTALL_ROOT="$1"
elif [ "x" = "x$INSTALL_ROOT" ]; then
    INSTALL_ROOT=/
fi

# Perhaps libexec could be used for those scripts, but many
# systems don't use libexec;
# The reason they won't go to /usr/sbin or the like is because
# they're not to be executed directly by the user
install -D -m744 vpn_wrapper.sh "$INSTALL_ROOT"/var/lib/0tdns/vpn_wrapper.sh
install -D -m744 netns-script "$INSTALL_ROOT"/var/lib/0tdns/netns-script

# simillar approach will be used to install other files
