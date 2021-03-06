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
install -D -m744 src/vpn_wrapper.sh "$INSTALL_ROOT"/var/lib/0tdns/vpn_wrapper.sh
install -D -m744 src/netns-script "$INSTALL_ROOT"/var/lib/0tdns/netns-script
install -D -m755 src/perform_queries.py "$INSTALL_ROOT"/var/lib/0tdns/perform_queries.py
install -D -m644 db_connection_config.yml "$INSTALL_ROOT"/etc/0tdns/db_connection_config.yml

# Those would make sense to be executed directly, so they'll go to (s)bin
# Those happen to also be the scripts, that get called by cron
install -D -m744 src/hourly.py "$INSTALL_ROOT"/usr/sbin/hourly.py
install -D -m744 src/check_if_done.py "$INSTALL_ROOT"/usr/sbin/check_if_done.py
install -D -m744 src/send_emails.py "$INSTALL_ROOT"/usr/bin/send_emails.py

# This one shall be imported from other scripts
install -D -m644 src/ztdnslib.py "$INSTALL_ROOT"/usr/lib/python3/dist-packages/ztdnslib.py

# simillar approach will be used to install other files
