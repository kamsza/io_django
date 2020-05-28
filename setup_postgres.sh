#!/bin/sh

echo "Creating 'ztdns' role"
sudo -u postgres createuser --no-createdb --no-createrole \
     --no-superuser --pwprompt ztdns

echo "Creating 'ztdns' database"
sudo -u postgres createdb -O ztdns ztdns
