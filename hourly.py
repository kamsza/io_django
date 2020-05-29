#!/bin/python3

from sys import argv
import subprocess

wrapper = '/var/lib/0tdns/vpn_wrapper.sh'
perform_queries = '/var/lib/0tdns/perform_queries.py'

def get_vpn_connections(hour):
    # TODO query database for the necessary information,
    # for now, return some sample though-up data
    return (
        # vpn_id | config_path
        (14,       "./vpngate_178.254.251.12_udp_1195.ovpn"),
        (13,       "./vpngate_public-vpn-229.opengw.net_tcp_443.ovpn")
    )

hour = argv[1]
for vpn_id, config_path in get_vpn_connections(hour):
    subprocess.run([wrapper, config_path, perform_queries, hour])
