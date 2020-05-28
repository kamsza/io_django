#!/bin/sh

echo "Dropping 'ztdns' database and role"
cat | sudo -u postgres psql <<EOF
drop database ztdns;
drop role ztdns;
EOF
