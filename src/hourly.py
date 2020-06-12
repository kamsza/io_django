#!/bin/python3

from sys import argv
import subprocess
from os import path
from time import gmtime, strftime

# our own module used by several scripts in the project
from ztdns_db_connectivity import start_db_connection, \
    get_default_host_address, get_ztdns_config

wrapper = '/var/lib/0tdns/vpn_wrapper.sh'
perform_queries = '/var/lib/0tdns/perform_queries.py'

def sync_ovpn_config(cursor, vpn_id, config_path, config_hash):
    cursor.execute('''
    select ovpn_config
    from user_side_vpn
    where id = %s and ovpn_config_sha256 = %s
    ''', (vpn_id, config_hash))
    
    (config_contents,) = cursor.fetchone()

    print(config_contents.tobytes())

    with open(config_path, "wb") as config_file:
        config_file.write(config_contents.tobytes())

def get_vpn_connections(cursor, hour):
    # return (
    #     # vpn_id | config_path
    #     (14,       "./vpngate_178.254.251.12_udp_1195.ovpn"),
    #     (13,       "./vpngate_public-vpn-229.opengw.net_tcp_443.ovpn")
    # )
    cursor.execute('''
    SELECT DISTINCT v.id, v.ovpn_config_sha256
    FROM user_side_queries AS q JOIN user_side_vpn AS v
    ON v.id = q.vpn_id;
    ''')
    return cursor.fetchall()

ztdns_config = get_ztdns_config()
if ztdns_config['enabled'] != 'yes':
    exit()

connection = start_db_connection(ztdns_config)
cursor = connection.cursor()

# round down to an hour - this datetime format is one
# of the formats accepted by postgres
hour = strftime('%Y-%m-%d %H:00', gmtime())

vpns = get_vpn_connections(cursor, hour)

handled_vpns = ztdns_config['handled_vpns']
if handled_vpns:
    vpns = [vpn for vpn in vpns if vpn[0] in handled_vpns]

for vpn_id, config_hash in vpns:
    config_path = "/var/lib/0tdns/{}.ovpn".format(config_hash)
    if not path.isfile(config_path):
        sync_ovpn_config(cursor, vpn_id, config_path, config_hash)

cursor.close()
connection.close()

for vpn_id, config_hash in vpns:
    config_path = "/var/lib/0tdns/{}.ovpn".format(config_hash)
    physical_ip = get_default_host_address(ztdns_config['host'])
    route_through_veth = ztdns_config['host'] + "/32"
    command_in_namespace = [perform_queries, hour, str(vpn_id)]
    print('RUNNING OPENVPN FOR {}'.format(vpn_id))
    subprocess.run([wrapper, config_path, physical_ip,
                    route_through_veth] + command_in_namespace)
